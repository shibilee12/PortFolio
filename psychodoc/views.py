from .utils import analyze_sentiment
from .models import JournalEntry, MoodEntry
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.timezone import localtime
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import datetime
import json
import os
try:
    from huggingface_hub import InferenceClient
    # Instantiate huggingface client once (set HF_TOKEN in environment variables)
    client = InferenceClient(api_key=os.environ.get("HF_TOKEN"))
except ImportError:
    client = None
    print("HuggingFace Hub not installed. AI features disabled.")
except Exception as e:
    client = None
    print(f"Error initializing InferenceClient: {e}")


@login_required
def journal(request):
    if request.method == "POST":
        content = request.POST.get('content', '').strip()
        if content:
            sentiment = analyze_sentiment(content)
            JournalEntry.objects.create(
                user=request.user if request.user.is_authenticated else User.objects.first(),
                content=content,
                sentiment=sentiment
            )
        return redirect('psychodoc_journal')

    entries = JournalEntry.objects.filter(user=request.user).order_by('-date')[:15]

    # Count of sentiments for visualization
    sentiments = {'Positive': 0, 'Neutral': 0, 'Negative': 0}
    for entry in entries:
        if entry.sentiment in sentiments:
            sentiments[entry.sentiment] += 1

    return render(request, 'journal.html', {
        'entries': entries,
        'sentiments': sentiments
    })

@login_required
def dashboard(request):
    if request.method == "POST":
        mood = request.POST.get('mood')
        notes = request.POST.get('notes', '').strip()
        sentiment = analyze_sentiment(notes) if notes else 'Neutral'
        MoodEntry.objects.create(
            user=request.user if request.user.is_authenticated else User.objects.first(),
            mood=mood,
            notes=notes,
            sentiment=sentiment
        )
        return redirect('psychodoc_dashboard')

    mood_choices = MoodEntry.MOOD_CHOICES
    entries = MoodEntry.objects.all().order_by('-date')
    return render(request, 'psychodoc.html', {
        'mood_choices': mood_choices,
        'entries': entries,
    })

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Auto-login after signup
            return redirect('psychodoc_dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

@login_required(login_url='psychodoc_login')
def mood_data(request):
    entries = MoodEntry.objects.all().order_by('date')
    mood_map = {}
    for entry in entries:
        dt = entry.date
        # If it's already a date, use it. Otherwise, convert.
        if isinstance(dt, datetime.datetime):
            date_val = localtime(dt).date()
        else:  # it's a datetime.date
            date_val = dt
        date_str = date_val.strftime('%Y-%m-%d')

        if date_str not in mood_map:
            mood_map[date_str] = {'happy': 0, 'neutral': 0, 'sad': 0, 'angry': 0, 'anxious': 0}
        mood_map[date_str][entry.mood] += 1

    dates = sorted(mood_map.keys())
    datasets = {mood: [] for mood in ['happy', 'neutral', 'sad', 'angry', 'anxious']}
    for date in dates:
        for mood in datasets:
            datasets[mood].append(mood_map[date][mood])

    return JsonResponse({'dates': dates, 'datasets': datasets})

@csrf_exempt
def ai_chat(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            messages = data.get('messages', None)
            if not messages or not isinstance(messages, list):
                return JsonResponse({'error': 'Messages are required'}, status=400)

            user_message = next((m.get("content") for m in reversed(messages) if m.get("role") == "user"), "")

            emotional_keywords = [
                "sad", "broken", "hurt", "depressed", "alone", "cry", "crying", "lost", "hopeless",
                "anxious", "anxiety", "panic", "heartbroken", "worthless", "empty", "pain",
                "breakup", "grief", "fear", "scared", "stressed", "angry", "numb", "guilty"
            ]

            if any(word in user_message.lower() for word in emotional_keywords):
                tone_instruction = (
                    "User is expressing emotional pain or sadness. "
                    "Respond with deep empathy, emotional validation, and gentle reassurance. "
                    "Acknowledge their feelings, offer comfort, and remind them they're not alone. "
                    "Avoid generic advice or robotic tone. Speak softly and sincerely."
                )
            else:
                tone_instruction = (
                    "User seems neutral or positive. Keep tone friendly, calm, and conversational. "
                    "Be supportive but natural — not overly emotional."
                )

            system_prompt = {
                "role": "system",
                "content": (
                    "You are PsychoDoc — an empathetic, emotionally intelligent companion. "
                    "Your goal is to comfort and emotionally support the user. "
                    "Always sound human, gentle, and caring — like a friend who truly listens. "
                    "Use natural language (no robotic phrasing). Keep responses short (2–4 sentences), "
                    "emotionally rich, and never reveal your internal reasoning. "
                    + tone_instruction
                )
            }

            if messages[0]['role'] != 'system':
                messages.insert(0, system_prompt)
            else:
                messages[0] = system_prompt

            if client is None:
                ai_reply = "I'm sorry, my AI brain is currently offline. Please check the server configuration."
            else:
                response = client.chat.completions.create(
                    model="meta-llama/Meta-Llama-3-8B-Instruct",
                    messages=messages,
                    max_tokens=250,
                    temperature=1.0,
                    top_p=0.95,
                )
                ai_reply = getattr(response.choices[0].message, 'content', "I'm here for you.")

            forbidden_phrases = ["I need to", "I should", "Let's think", "My goal is", "I will try to"]
            if any(p in ai_reply for p in forbidden_phrases):
                ai_reply = ai_reply.split("\n")[-1].strip()

            return JsonResponse({'reply': ai_reply})

        except Exception as e:
            print("AI ERROR:", str(e))
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
def analyze_journal_with_ai(request):
    try:
        entries = JournalEntry.objects.filter(user=request.user).order_by('-date')[:15]

        if not entries.exists():
            return JsonResponse({'response': "You don't have any journal entries yet."})

        combined_text = "\n".join([f"- {e.content}" for e in entries])

        prompt = (
            "You are PsychoDoc, an empathetic AI therapist.\n"
            "Analyze the following journal entries and summarize the user's current mood trends, "
            "possible emotional challenges, and gentle advice for improvement.\n"
            "Be concise, warm, and supportive.\n\n"
            f"Entries:\n{combined_text}\n\nYour analysis:"
        )

        if client is None:
            result = "AI analysis is currently unavailable."
        else:
            response = client.chat.completions.create(
                model="mistralai/Mixtral-8x7B-Instruct-v0.1",  # reliable model for analysis
                messages=[{"role": "user", "content": prompt}],
                max_tokens=250,
                temperature=0.7,
            )
            result = response.choices[0].message.content.strip()
        return JsonResponse({'response': result})

    except Exception as e:
        print("AI Analysis Error:", str(e))
        return JsonResponse({'response': "Sorry, PsychoDoc couldn't analyze right now."})
    
@login_required
def reflect_with_ai(request):
    entries = JournalEntry.objects.filter(user=request.user).order_by('-date')[:10]
    if not entries:
        return JsonResponse({'reply': "You haven't written any journal entries yet."})

    # Combine all journal content
    combined_text = "\n\n".join([f"- {e.content}" for e in entries])

    prompt = f"""
    You are PsychoDoc, an empathetic mental health companion.
    The following are journal entries from a user over several days.
    Read them carefully and identify emotional patterns, mood shifts, or recurring thoughts.
    Respond with empathy and reflection — speak as if you're helping them understand themselves.
    Be gentle, insightful, and validating. Don't summarize mechanically — reflect emotionally.

    Journal Entries:
    {combined_text}

    Respond with a compassionate summary of their emotional state and what they might need right now.
    """

    try:
        if client is None:
            reply = "I'm unavailable right now, but please keep writing."
        else:
            response = client.chat.completions.create(
                model="meta-llama/Meta-Llama-3-8B-Instruct",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=350,
                temperature=0.9,
            )
            reply = getattr(response.choices[0].message, 'content', '').strip()
        
        if not reply:
            reply = "I sense that you're going through a lot. It's okay to feel everything — take your time to heal."
        return JsonResponse({'reply': reply})
    except Exception as e:
        print("AI reflection error:", e)
        return JsonResponse({'reply': "Sorry, I couldn't process your journals right now."})