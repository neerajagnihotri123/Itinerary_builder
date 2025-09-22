# Travello.ai - AI Travel Concierge

A comprehensive AI-powered travel planning application with dynamic pricing, multi-agent system, and personalized itinerary generation.

## Updated Project Structure

```
/app/
├── backend/                 # FastAPI backend
│   ├── .env
│   ├── requirements.txt
│   ├── server.py            # Main FastAPI application
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── context_store.py
│   │   └── event_bus.py
│   └── agents/
│       ├── __init__.py
│       ├── profile_intake_agent.py
│       ├── persona_classification_agent.py
│       ├── itinerary_generation_agent.py
│       ├── customization_agent.py
│       ├── pricing_agent.py
│       ├── external_booking_agent.py
│       ├── sustainability_seasonality_agent.py
│       ├── service_selection_agent.py
│       ├── conflict_detection_agent.py
│       └── dynamic_pricing_agent.py
├── frontend/                # React frontend
│   ├── .env
│   ├── package.json
│   ├── public/
│   └── src/
│       ├── components/      # Reusable UI components
│       │   ├── ui/          # Modal components, buttons, etc.
│       │   │   ├── CheckoutModal.js
│       │   │   ├── RequestCallbackModal.js
│       │   │   ├── TripHistoryModal.js
│       │   │   ├── PricingBreakdownModal.js
│       │   │   ├── ServiceSelectionDropdown.js
│       │   │   ├── ConflictWarnings.js
│       │   │   ├── SafeImage.js
│       │   │   └── [shadcn/ui components...]
│       │   └── layout/      # Header, footer, layout components
│       ├── pages/           # Page-level components 
│       │   └── Home.js      # Main travel planning page
│       ├── App.js           # Main app with routing setup
│       ├── index.js         # Entry point
│       ├── assets/          # Images, icons, static files
│       ├── styles/          # CSS files (App.css, etc.)
│       │   ├── App.css
│       │   └── index.css
│       ├── utils/           # Helper functions, API calls
│       │   ├── imageUtils.js
│       │   └── utils.js
│       └── hooks/           # Custom React hooks
│           └── use-toast.js
├── scripts/
├── tests/
└── docs/
    ├── TRAVELLO_AI_UPDATED_TECHNICAL_DOCUMENTATION.md
    └── AGENT_UPGRADE_IMPLEMENTATION_PLAN.md
```

## Recent Changes

### ✅ Folder Structure Reorganization (September 2025)
- **Modularized Frontend**: Extracted components from the large App.js file into organized folders
- **UI Components**: Moved modal components to `components/ui/` folder
- **Utilities**: Centralized helper functions in `utils/` folder  
- **Styles**: Organized CSS files in `styles/` folder
- **Maintained Functionality**: All existing features preserved during restructuring

### Key Extracted Components:
- `CheckoutModal.js` - Payment processing modal
- `RequestCallbackModal.js` - Contact form for expert consultation
- `TripHistoryModal.js` - Saved trips management
- `PricingBreakdownModal.js` - Dynamic pricing display
- `ServiceSelectionDropdown.js` - Service selection interface
- `ConflictWarnings.js` - Itinerary conflict detection
- `SafeImage.js` - Image component with fallback handling

### Utility Functions:
- `imageUtils.js` - Image proxying and fallback logic
- `utils.js` - General utility functions

## Tech Stack

- **Frontend**: React, Tailwind CSS, Framer Motion
- **Backend**: FastAPI, Python
- **Database**: MongoDB
- **Architecture**: Multi-agent event-driven system
- **LLM Integration**: Emergent LLM Key support

## Running the Application

```bash
# Backend and Frontend are managed by supervisor
sudo supervisorctl status
sudo supervisorctl restart all
```

## Development Guidelines

1. **Component Organization**: Place reusable components in `components/ui/`
2. **Page Components**: Main page logic goes in `pages/`
3. **Utilities**: Helper functions in `utils/`
4. **Styles**: CSS files in `styles/`
5. **Import Structure**: Use relative imports for better maintainability
