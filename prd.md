# Product Requirements Document

## AI Based Sustainable Lifestyle Recommendation Platform

## 1. Purpose

This PRD translates the project report into a product plan for a Streamlit application that helps people in India understand their lifestyle carbon footprint and choose practical ways to reduce it. The report describes an early prototype and intended work; this document distinguishes those stated capabilities from recommended additions.

## 2. Problem

People often receive generic sustainability tips or a footprint total without clear, personalized next steps. The product should identify a user's larger sources of emissions, recommend feasible actions, explain the evidence behind estimated impact, and help the user track changes.

## 3. Users

- Students and individuals seeking practical sustainability guidance.
- Indian urban households with differing transport, housing, budget, and service access.
- Project evaluators assessing calculation accuracy, recommendation relevance, and usability.

## 4. Product goals and success measures

From the report:
- Estimate annual footprint across transport, diet, household energy, shopping, and waste using published emission factors.
- Provide at least five ranked, personalized actions.
- Keep estimates within 10% of manual calculations on 20 test profiles.
- Have at least 80% of recommendations rated relevant and feasible.
- Target a complete report response time below 10 seconds and usability rating of at least 4/5 among 30 student users.

Recommended product measures:
- Questionnaire completion and recommendation acceptance rates.
- Percentage of recommendations with traceable source and last-reviewed date.
- Goal completion rate and profile refresh rate.
- Explanation validation failure and fallback rates.

## 5. Scope

### MVP capabilities described in the report

1. Lifestyle questionnaire covering activity habits, location, budget, housing type, and preferences, with validation.
2. Annual footprint estimate and category breakdown using rule-based calculations and published factors.
3. Curated action catalogue with estimated annual CO2e savings, INR cost or savings, difficulty, applicability, and source.
4. Applicability filtering and weighted ranking by impact, cost, ease, and preference match.
5. Plain-language LLM explanations grounded in the selected catalogue data, with structured output validation and template fallback.
6. Dashboard with ranked recommendations, footprint charts, user-selected goals, progress updates, recalculation, and milestone badges.
7. SQLite persistence for progress tracking; Streamlit deployment and user documentation.

The report says the estimation and scoring backend and an initial catalogue of about 30 actions are implemented. The interface, expanded catalogue, explanation layer, tracking, evaluation, and deployment remain planned work.

### Recommended additions

Prioritize after the MVP unless time allows:
- **Guest mode and privacy controls:** explain what is stored, allow data export and account deletion, and support local-only use where practical.
- **Uncertainty ranges:** show estimates as approximate ranges where activity data or emission factors are uncertain; explain major assumptions.
- **Factor and catalogue governance:** store source URL, geography, year, unit, method, reviewer, and review date; flag stale entries.
- **Action alternatives:** show lower-cost or easier alternatives when a top action is unaffordable or unavailable.
- **What-if planner:** compare scenarios such as two versus three car-free commute days before committing.
- **Regional availability:** allow users to mark metro, bus, cycling, composting, and rooftop solar availability; avoid assuming every city offers the same services.
- **Accessibility and language:** keyboard support, readable contrast, mobile-friendly layout, and a later phase for Indian language translations.
- **Reminders and check-ins:** optional weekly or monthly prompts to update progress, with opt-in controls.
- **Shareable summary:** export a private PDF or CSV of footprint, assumptions, goals, and progress.
- **Admin/evaluation mode:** manage catalogue entries and collect consented, anonymized usability feedback.

## 6. Core user journey

1. User opens the app and reads a short explanation of estimates and data handling.
2. User enters location and lifestyle information, skipping unknown or irrelevant questions where possible.
3. The app validates answers and calculates an annual footprint by category.
4. The app filters inapplicable actions and ranks the remaining actions.
5. User reviews savings, approximate INR cost, difficulty, applicability, evidence, and explanation.
6. User selects one or more actions as goals and records progress.
7. Dashboard reflects progress and recalculates estimates when the user updates habits.

## 7. Functional requirements

- **FR1 Profile:** Capture transport, diet, energy, shopping, waste, location, monthly budget, housing tenure, and preferences. Validate units, bounds, and required fields.
- **FR2 Footprint:** Calculate annual kg CO2e per category and total, showing factor sources and calculation assumptions.
- **FR3 Catalogue:** Represent each action with stable ID, category, savings method/value, cost or savings in INR, difficulty, eligibility rules, evidence, and review metadata.
- **FR4 Ranking:** Exclude inapplicable actions; rank eligible actions using configurable, documented weights. Provide at least five where available.
- **FR5 Explanations:** LLM may explain only supplied action facts. Validate action IDs and numeric claims; retry up to the configured limit, then use a deterministic template.
- **FR6 Goals:** Let users add, pause, complete, or remove actions and record progress.
- **FR7 Dashboard:** Show total/category footprint, selected goals, progress history, and earned milestones.
- **FR8 Persistence:** Store only necessary user profile and progress data in SQLite; handle missing or reset data safely.
- **FR9 Performance:** Target end-to-end recommendation generation under 10 seconds; show useful loading and error states.
- **FR10 Evaluation:** Support reproducible test profiles and consented feedback collection without exposing personal data.

## 8. Non-functional requirements

- Explain that estimates are directional and depend on user inputs and factor quality.
- Keep numerical calculations outside the LLM; never treat generated prose as the source of impact figures.
- Keep API credentials in environment configuration, never in source control.
- Use accessible color contrast, clear units, responsive layouts, and understandable errors.
- Log operational errors without logging secrets or unnecessary personal answers.
- Make emission factors and scoring weights versioned and reproducible.

## 9. Out of scope for the first release

- Real-time utility, bank, transport, or shopping integrations.
- Verified measurement of actual emissions reductions.
- Social leaderboards or public sharing by default.
- Automated purchases, offsets, or claims of carbon neutrality.
- Collaborative filtering requiring a large user dataset.

## 10. Risks and mitigations

- **Factor mismatch by region/year:** label geography and year, use India-relevant sources where available, and expose assumptions.
- **False precision:** show approximate values and ranges where justified.
- **LLM hallucination:** constrain input, validate output, and fall back to templates.
- **Unusable recommendations:** collect availability and constraints; offer alternatives and feedback controls.
- **Low retention:** keep onboarding short and make progress tracking optional and useful.
- **Sensitive lifestyle data:** minimize collection, document storage, and provide delete/export controls.

## 11. Release plan

1. Complete Streamlit questionnaire, footprint breakdown, and recommendation cards.
2. Expand and document the catalogue; integrate grounded explanations and validation.
3. Add goals, SQLite tracking, progress charts, and badges.
4. Evaluate calculation accuracy on 20 profiles and relevance/usability with at least 30 students.
5. Refine based on results, deploy, and publish user documentation.
6. Consider recommended additions based on evaluation findings and available project time.

## 12. Open decisions

- Which emission-factor sources and update cadence are authoritative for each category?
- Will the first release support named accounts, or use a single-device profile?
- Which LLM provider and data-retention terms are acceptable for student use?
- What precisely defines an action as completed, and how will estimated savings be recalculated?
- Which language and accessibility requirements are mandatory for the project evaluation?
