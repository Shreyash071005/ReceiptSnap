import json
from google import genai
from google.genai import types
import streamlit as st
from twilio.rest import Client as TwilioClient

from prompts import (SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE, SUMMARY_REQUEST_PROMPT)

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_FROM = st.secrets["TWILIO_WHATSAPP_FROM"]
TWILIO_CONTENT_SID = st.secrets["TWILIO_CONTENT_SID"]
MODEL_NAME = "gemini-3.8-flash"

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)

@st.cache_resource
def get_twilio_client():
    return TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
 
 
gemini_client = get_gemini_client()
twilio_client = get_twilio_client()

def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])

        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role, kind, content):
    st.session_state.messages.append(
        {
            "role": role,
            "kind": kind,
            "content": content,
        }
    )
    render_message(st.session_state.messages[-1])


import time


def ask_gemini(parts, max_retries=4):
    for attempt in range(max_retries):

        try:
            response = st.session_state.chat.send_message(parts)
            return response.text

        except Exception as error:

            error_text = str(error)

            # Retry temporary Google server errors
            if "503" in error_text or "UNAVAILABLE" in error_text:

                if attempt < max_retries - 1:
                    delay = 2 ** attempt

                    time.sleep(delay)
                    continue

            return f"Sorry, something went wrong: {error}"

def clean_whatsapp_text(text):
    if not text:
        return "No nutrition summary available."
    text = " ".join(text.split())  # collapse whitespace/newlines
    return text[:1500] + "..." if len(text) > 1500 else text
 
 
def send_whatsapp(to_number, user_name, summary):
    # Content template expects {{1}} = name, {{2}} = summary.
    try:
        content_variables = json.dumps(
            {"1": user_name, "2": clean_whatsapp_text(summary)}, ensure_ascii=False
        )
        message = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to_number}",
            content_sid=TWILIO_CONTENT_SID,
            content_variables=content_variables,
        )
        return True, message.sid
    except Exception as error:
        return False, str(error)


# Step 1: Onboarding (username and phone)

if "onboarded" not in st.session_state:

    st.title("🧾 ReceiptSnap")
    st.caption("Scan it. Track it. Text yourself the results.")

    with st.form("onboarding_form"):

        name = st.text_input("Your name")

        whatsapp_number = st.text_input(
            "WhatsApp number (with country code)",
            placeholder="+91XXXXXXXXXX",
        )

        submitted = st.form_submit_button("Let's track 🚀")

    if submitted:

        if not name.strip() or not whatsapp_number.strip():

            st.warning(
                "Please fill in both your name and WhatsApp number."
            )

        else:

            st.session_state.name = name.strip()
            st.session_state.whatsapp_number = whatsapp_number.strip()

            st.session_state.chat = gemini_client.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT
                ),
            )

            st.session_state.messages = []
            st.session_state.onboarded = True

            st.rerun()

    st.stop()


# Step 2: Create the chat interface

header_col, button_col = st.columns([5, 2], vertical_alignment="center")

with header_col:
    st.title("🧾 ReceiptSnap")

with button_col:

    send_disabled = len(st.session_state.messages) <= 2

    if st.button("📤 Send to WhatsApp", disabled=send_disabled, use_container_width=True,):

        with st.spinner("Preparing your expense summary..."):
            summary = ask_gemini([SUMMARY_REQUEST_PROMPT])

        success, info = send_whatsapp(
            st.session_state.whatsapp_number,
            st.session_state.name,
            summary,
        )

        if success:
            st.success("Sent! Check your WhatsApp 📲")

        else:
            st.error(
                f"Couldn't send that: {info}"
            )


st.caption(
    f"Logged in as {st.session_state.name} - "
    f"expenses go to {st.session_state.whatsapp_number}"
)


# Step 3: Display welcome message or existing messages

if not st.session_state.messages:

    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE_TEMPLATE.format(
            name=st.session_state.name
        ),
    )

else:

    for message in st.session_state.messages:
        render_message(message)


# Step 4: Chat input

user_input = st.chat_input(
    "Describe an expense or attach a receipt photo",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)


if user_input:

    photo = (
        user_input.files[0]
        if user_input.files
        else None
    )

    text = user_input.text

    parts = []


    # Handle uploaded receipt photo

    if photo is not None:

        photo_bytes = photo.getvalue()

        add_message(
            "user",
            "image",
            photo_bytes,
        )

        parts.append(
            types.Part.from_bytes(
                data=photo_bytes,
                mime_type=photo.type,
            )
        )


    # Handle text input

    if text:

        add_message(
            "user",
            "text",
            text,
        )

        parts.append(text)


    # If only a receipt photo was uploaded

    elif photo is not None:

        parts.append(
            "Analyze this receipt and extract the "
            "merchant name, date, purchased items, "
            "total amount, and expense category. "
            "Clearly mention any information that "
            "cannot be read from the receipt."
        )


    # Send request to Gemini

    with st.spinner("Reading your receipt..."):
        answer = ask_gemini(parts)

    # Display Gemini response

    add_message("assistant", "text", answer)