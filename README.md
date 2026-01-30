# AI-Based-Risk-Assessment-Database-Tinker-AFB-
 

## Project Overview 
This project builds an AI-powered industrial risk assessment database to help manage environmental and occupational risks in depot maintenance facilities. The system evaluates hazards (hazardous materials/waste, environmental and health hazards), supports pollution prevention and recycling opportunities, and recommends mitigation strategies including PPE and engineering controls.   
 

## Key Goals 
- Centralize risk assessment data and reduce fragmented decision-making 
- Predict potential risks using historical data and machine learning 
- Support plain-language querying via NLP 
- Recommend tailored mitigation strategies, including PPE guidance 
 

## Key Feature (Current Focus) 
### PPE Recommendation System 
Given hazard characteristics (type, severity, exposure route), the system recommends appropriate PPE items with a short explanation. 
 

## Technologies 
- Backend API: FastAPI (Python) 
- Database: PostgreSQL 
- ML / Risk Prediction: scikit-learn (Python) 
- Frontend: React 
 

## Repository Structure 
- `/api` - FastAPI service 
- `/db` - schema + migrations 
- `/ml` - model training + evaluation 
- `/docs` - feature docs, meeting notes, research notes 
- `/tests` - automated tests 
 

## Progress Plan 
### Sprint 1 (Domain + Foundations) 
- Confirm hazard/PPE data fields 
- Draft database schema 
- Define PPE Recommendation MVP rules 
- Stand up API skeleton + health endpoint 
 

### Sprint 2 (MVP Build) 
- Implement PPE recommendation endpoint 
- Create seed data for PPE items/rules 
- Add unit tests + CI 
 

### Sprint 3 (Intelligence Layer) 
- Add baseline ML model for risk scoring (prototype) 
- Add NLP query prototype (basic intent extraction) 
 

## How to Run 
- Add setup steps once API/DB are initialized 
