# URA GO Portal (URA Dashboard)

An enterprise analytics and resource portal designed for the Uganda Revenue Authority (URA). The platform provides a centralized, role-based dashboard for managing resources, analytics, announcements, and governance.

## Tech Stack

### Frontend
- **Framework:** Next.js (React)
- **Language:** TypeScript
- **Styling:** CSS / Custom Components

### Backend
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL
- **Authentication:** Session-based (with bcrypt for password hashing)

## Features
- **User Authentication & RBAC:** Secure login/registration with role-based access control (Admin vs. Standard User). Account requests require admin approval.
- **Multi-Department Context:** Users can belong to multiple departments and switch their active working context seamlessly.
- **Resource Management:** Upload, organize, and manage internal resources and files.
- **Enterprise Analytics:** Centralized data visualization and metrics.
- **Announcements & Governance:** Internal communication and policy tracking.
- **AI Chatbot:** Intelligent assistance integrated directly into the portal.
- **Transactional Emails:** Automated SMTP email notifications for account lifecycle events (approvals, rejections, password resets).

## Local Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL server

### Backend Setup
1. Navigate to the root directory.
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables in a `.env` file based on `.env.save` (database credentials, SMTP config, etc.).
5. Run the FastAPI server:
   ```bash
   uvicorn backend.main:app --reload
   ```
   *The API will be available at `http://localhost:8000`*

### Frontend Setup
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
   *The frontend will be available at `http://localhost:3000`*

## Deployment
This project is configured for deployment on platforms like Render. 
- The backend relies on standard ASGI deployment (e.g., Uvicorn).
- The frontend is a standard Next.js application that can be deployed on Render, Vercel, or Netlify.

## License
&copy; Uganda Revenue Authority. All rights reserved.
