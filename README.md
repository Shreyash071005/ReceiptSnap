# ReceiptSnap — AI Receipt and Expense Tracker

ReceiptSnap is an AI-powered receipt and expense tracking application built using Streamlit and Google Gemini.

The application allows users to upload receipt images or describe expenses using natural language. Google Gemini analyzes the provided information and extracts relevant expense details such as merchant name, purchase date, purchased items, total amount, currency, and expense category.

ReceiptSnap also integrates with WhatsApp through Twilio, allowing users to receive their expense summaries directly on WhatsApp.

## Features

- AI-powered receipt analysis using Google Gemini
- Upload receipt images in JPG, JPEG, PNG, and WEBP formats
- Extract merchant name, purchase date, items, quantities, prices, tax/GST, discounts, total amount, currency, and category
- Add expenses using natural language descriptions
- Generate consolidated expense summaries
- Send expense summaries directly to WhatsApp
- Twilio WhatsApp integration
- User identification using name and mobile number
- Session-based expense tracking
- Retry handling for temporary Gemini API errors
- Streamlit-based web interface
- Secure storage of API credentials using Streamlit Secrets

## Technology Stack

| Technology | Purpose |
|------------|---------|
| Python | Application development |
| Streamlit | Web application interface |
| Google Gemini | Receipt and expense analysis |
| Google GenAI SDK | Gemini API integration |
| Twilio | WhatsApp messaging |
| WhatsApp | Expense summary delivery |
| Requests | HTTP communication |
| Pillow | Image handling |

## Application Workflow

```text
                    ┌──────────────────┐
                    │    ReceiptSnap   │
                    └────────┬─────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
          Upload Receipt            Describe Expense
                │                         │
                └────────────┬────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Google Gemini   │
                    │  AI Analysis     │
                    └────────┬─────────┘
                             │
                             ▼
                    Expense Information
                             │
                             ▼
                    ┌──────────────────┐
                    │ Expense Summary  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │      Twilio      │
                    │ WhatsApp API     │
                    └────────┬─────────┘
                             │
                             ▼
                    User's WhatsApp