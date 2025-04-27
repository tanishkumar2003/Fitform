# Fitform

A fitness tracking application with AI-powered features for workout optimization.

## Project Structure

```
fitness-ai-app/
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── requirements.txt
│   └── utils/
│       └── predictive_analysis.py
├── .gitignore
└── README.md
```

## Setup Instructions

1. Create virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r backend/requirements.txt
```

3. Set up MongoDB:

- Create a MongoDB Atlas cluster
- Create .env file with your MongoDB connection string:

```
MONGO_URI="mongodb+srv://<username>:<password>@cluster.mongodb.net/fitnessai?retryWrites=true&w=majority"
```

## Running the Application

1. Start the Backend:

```bash
cd backend
uvicorn app:app --reload
```

The backend will run on http://localhost:8000

2. Start the Frontend:

```bash
cd frontend
python -m http.server 8080
```

The frontend will be available at http://localhost:8080

3. Testing the Setup:

- Open http://localhost:8080 in your browser
- Try creating a journal entry
- Check the Network tab in browser DevTools for API calls
- Visit http://localhost:8000/health to verify backend status

## API Documentation

### Journaling Endpoints

- `POST /journal/entry` - Create new journal entry
- `GET /journal/entries/{user_id}` - Get all entries for a user
- `GET /journal/entries/{user_id}/{date}` - Get entry by date
- `GET /journal/suggestions/{user_id}` - Get AI-powered exercise suggestions
