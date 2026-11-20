# Product Requirements Document

## AI-Based Sustainable Lifestyle Recommendation Platform

**Status:** Product plan for the current academic prototype
**Primary platform:** Python and Streamlit web application
**Primary audience:** Indian college students and households exploring practical sustainability habits

## 1. Product summary

The platform helps a person estimate selected parts of their annual lifestyle greenhouse gas footprint, understand the limitations of that estimate, find sustainable actions that fit their stated habits, and track actions they choose to try. It combines documented-factor calculations, a content-based action recommender, and SQLite persistence in a modular Streamlit application.

The product must distinguish measured inputs, calculated estimates, qualitative recommendations, and future features. It must not present a recommendation match score as a probability, claim unverified emissions savings, or imply that a partial footprint represents a complete environmental impact.

## 2. Problem and opportunity

People often encounter generic sustainability advice or a carbon total without a clear explanation of its sources and practical next steps. A useful student-scale product can connect a simple lifestyle profile to transparent estimates and relevant actions, while showing where data is incomplete.

The project is also an opportunity to demonstrate practical software engineering and AI/ML: modular UI, input validation, documented calculations, text similarity, structured persistence, evaluation, and responsible data handling.

## 3. Product goals

1. Help users understand their activity inputs and the limits of the resulting estimate.
2. Show an annual category breakdown from supported activity data and documented factors.
3. Rank actions using the existing TF-IDF and cosine-similarity recommender, profile constraints, and catalogue metadata.
4. Let users save, update, complete, and remove goals, with history persisted in SQLite.
5. Make important information easy to find and use on desktop and mobile-sized screens.
6. Keep the prototype technically manageable for a third-year B.Tech AI/ML project.

## 4. Users and use cases

### Primary users

- **Student or individual:** wants practical actions that match their routine, budget, home, and local availability.
- **Project evaluator:** wants to inspect the architecture, factors, recommendation method, evaluation, and working application.
- **Project maintainer:** needs to update factors and actions with traceable sources and preserve data integrity.

### Core use cases

- Create an account and return to saved profile and goal data.
- Complete or update a lifestyle questionnaire.
- Enter activity quantities and inspect a partial annual footprint estimate.
- Understand which categories are included and why water or waste may be displayed separately.
- Review and save relevant actions as goals.
- Track goal progress and compare multiple saved estimates.
- Read the source and assumptions behind calculations and catalogue actions.

## 5. Current product baseline

This section describes the repository as it exists today, to distinguish implemented behavior from proposed work.

| Area | Current implementation | Important limitation |
|---|---|---|
| UI and navigation | Streamlit pages for Home, Login/Register, Questionnaire, Dashboard, Recommendations, Carbon footprint, Progress, and Profile | Desktop-first visual layout; responsive behavior and accessibility need hands-on review |
| Accounts | Local SQLite user records; passwords stored as salted PBKDF2 hashes; sign-out and account deletion controls | No recovery flow, rate limiting, external identity provider, or deployment-grade session management; legacy passwordless accounts cannot sign in through the new flow |
| Questionnaire | Collects commute, diet, home, budget, energy, waste, shopping, water-use habits, and availability preferences; saves responses | Inputs are not yet the sole source of calculator activity quantities; asking users to repeat activity data can be confusing |
| Footprint calculator | Calculates transportation fuel combustion, grid electricity, and food emissions from CSV factors; reports water and waste as resource indicators; saves activity input snapshots | Partial categories and mixed system boundaries; no public transit, upstream fuel, detailed household allocation, or locally matched water/waste emissions factors |
| Recommendations | Curated catalogue ranked with TF-IDF/cosine similarity, eligibility rules, and documented reranking; can save an action as a goal | Fit score is not confidence; no verified personalized kg CO₂e savings are available |
| Dashboard | Reads saved estimates, goals, and recommendations; avoids invented scores and savings | No defined sustainability score or comprehensive time-series analysis |
| Progress | Persists goal progress and displays a trend after multiple saved estimates | Trend can be misleading when factors or user input methods differ; no periodic reminders or evidence of actual behavior change |
| Persistence | SQLite stores users, questionnaire responses, estimates, recommendations, and progress | Local single-file database; no export/delete controls or backup workflow in the UI |
| Evaluation | Small hand-labeled recommender scenario set and repeatable smoke checks | Evaluation is not a user study and does not establish population-level relevance |

### Implemented from this PRD

- Home directs first-time users to the questionnaire; new registrations continue to the questionnaire, and saving offers a direct path to the calculator.
- Saved questionnaire electricity pre-fills the calculator. Other activity quantities are never inferred from commute distance or qualitative answers.
- Each new estimate stores the input snapshot needed to reload calculator entries. Trend charts compare only estimates with the same factor set and supported input-snapshot format.
- Recommendation cards identify their applicability rule and source, label relevance as profile fit, and state that quantified savings are not available. Actions already in a user's goals cannot be added a second time.
- Sidebar account controls include sign-out. Profile includes JSON export and confirmed account/data deletion.
- Shared styling now includes responsive spacing and visible keyboard-focus treatment; actual device/browser accessibility review remains to be performed.
- Page-level failures use concise messages while diagnostics are written to the application log.

The feature roadmap below remains a plan. In particular, action feedback learning, scenario comparison, goal target dates/reminders, PDF reporting, regional factors, localization, and optional LLM explanations have not been implemented.

## 6. Product principles

- **Explain the estimate:** show units, included categories, source geography/year, and assumptions close to the result.
- **Be honest about uncertainty:** use “estimate” and avoid implying verified reductions or complete coverage.
- **Make actions feasible:** account for transport access, home constraints, budget, and user preferences.
- **Give users control:** allow skipping unknown answers, editing inputs, and choosing whether to save an action.
- **Keep the experience calm:** make one useful next step clear instead of filling the screen with scores and charts.
- **Protect personal data:** collect only what is needed, explain local storage, and provide a practical way to delete or export it.

## 7. Proposed features and priorities

Priorities are ordered for a mini-project delivery. P0 improves correctness and clarity in the existing flow; P1 adds useful capabilities; P2 is optional if time permits.

### P0 — Make the existing experience coherent and trustworthy

1. **Guided first-use flow:** welcome → privacy/estimate note → questionnaire → calculator → recommendations. Preserve the ability to skip and use sidebar navigation.
2. **Questionnaire-to-calculator connection:** prefill supported calculator fields from saved profile information. Ask only for quantities that the questionnaire does not collect. Clearly identify prefilled values and let users edit them.
3. **Estimate completeness indicator:** show included categories, categories not yet covered, missing inputs, factor set, and last calculation date with every saved estimate.
4. **Comparable estimate history:** show a trend only when estimates use compatible factor versions and comparable inputs. Otherwise explain the difference and show individual records without a connected trend line.
5. **Recommendation action details:** provide a short “Why this fits” explanation, eligibility conditions, source link, effort, cost tier, and an explicit note that no quantified savings are currently estimated.
6. **Account and profile controls:** add sign out, a clear demo/registered-account label, and helpful handling of legacy accounts without passwords. Never silently switch a user to a different profile.
7. **Data management:** allow account/profile deletion with confirmation and provide a downloadable copy of questionnaire responses, estimates, and goals.
8. **Form and error states:** preserve entered values after validation failures, identify the field that needs attention, and provide retry guidance without exposing stack traces or database internals.

### P1 — Improve personalization and follow-through

1. **Recommendation feedback:** let users mark an action “relevant,” “not for me,” or “already doing this.” Use this feedback to improve session ranking without claiming model learning until evaluation supports it.
2. **Alternative actions:** for an unavailable, costly, or difficult action, show a lower-cost or easier catalogue alternative in the same category.
3. **Goal planning:** let a user set a target date and a simple weekly/monthly check-in, pause a goal, and add an optional note.
4. **Scenario planner:** allow side-by-side comparison of a small number of user-editable activity scenarios (for example, electricity use before/after). Label these as hypothetical estimates; do not count them as achieved progress.
5. **Category guidance:** add concise category explanations and “what you can change” links from the footprint chart to relevant actions.
6. **Factor transparency panel:** show factor name, value, unit, source, geography, reference year, and limitations in a compact, consistent detail view.
7. **Optional report export:** create a local PDF or CSV summary containing input date, factor version, category results, assumptions, and selected goals.

### P2 — Extend only when evidence and project time support it

1. **More regional factors:** add city/state or more locally relevant datasets when authoritative factors are available and documented.
2. **More activity categories:** investigate housing fuels, public transport, additional food groups, and waste pathways; add them only with sufficiently reliable factors and user inputs.
3. **Localization:** translate key onboarding and action copy into selected Indian languages after terminology review.
4. **Optional reminders:** opt-in local or email reminders for goal check-ins, with easy disable controls.
5. **Admin catalogue editor:** provide a maintainer workflow to validate action metadata, sources, and review dates before publication.
6. **Grounded language explanations:** consider an LLM only if API secrets, privacy implications, output checks, fallback behavior, and demo cost are all addressed. Deterministic explanations are sufficient for the core project.

## 8. Improvements to existing features

### Home and onboarding

- State the product’s purpose in one sentence and distinguish estimates from verified measurements.
- Use a primary call to action (“Build my profile”) and a secondary one (“Explore the demo”).
- Show the three-step journey and disclose that data is stored locally in SQLite.
- Remove sample-value wording where the page uses real saved data; identify any example content explicitly.

### Registration and sign-in

- Explain password requirements before submission and keep the confirmation field only for registration.
- Provide show/hide password controls, field-level validation, and a generic incorrect-credentials message.
- Add a sign-out control and clear the in-memory profile cache on account change.
- State plainly that account recovery is not available in this academic prototype. Do not call local authentication production-ready.
- Add a confirmation dialog before deleting an account and associated records.

### Lifestyle questionnaire

- Break the form into short steps: location and transport; home and energy; food and waste; budget and preferences.
- Add a progress indicator, “Back,” “Continue,” and “Save for later” behavior while preserving current answers.
- Put units and examples next to numeric inputs; validate plausible ranges and explain why a value is needed.
- Allow “Not sure” for answers the recommendation model can safely handle as unknown.
- On save, summarize what was saved and link to the next useful step.

### Carbon footprint calculator

- Group inputs by category with clear time bases such as litres/month, kWh/month, and kg/week.
- Prefill only values directly supported by the saved questionnaire; never infer vehicle fuel from commute distance without an explicit vehicle/fuel assumption.
- Explain that zero means “no amount entered” where appropriate.
- Put the partial-total label, included categories, and limitations next to the headline number.
- Use a bar chart for category comparisons; keep the table available for exact values and accessible alternatives.
- Separate water and waste indicators from emissions and retain their data when saving an estimate so users can compare resource use later.
- Show a “Save estimate” confirmation and the factor version used. Avoid silently overwriting earlier records.

### Recommendations

- Sort action cards by a visible and understandable relevance rank while allowing category filters.
- Keep the match explanation, source, applicability, effort, and cost tier in a predictable location on each card.
- Use a progress bar only if accompanied by a label that says it is a profile match score, not confidence or impact.
- Disable or change the Add goal button after an action is saved, and show a direct link to that goal.
- Provide empty/error states if no action is eligible or if the catalogue cannot load.

### Dashboard and progress

- Use one primary metric: the latest saved partial annual estimate, or a clear prompt to calculate one.
- Show category contributions, estimate date, factor version, and comparability warning where needed.
- Keep goal counts and “next action” cards tied to SQLite records; do not show unsupported savings or sustainability scores.
- Use an empty-state trend message until enough compatible records exist.
- In progress tracking, make status and progress understandable together; provide undo or confirmation for destructive actions.

### Profile

- Distinguish saved account details from questionnaire answers and offer clear edit actions.
- Show data export and delete controls with plain-language explanations.
- Avoid describing persisted fields as temporary session data.

## 9. UI/UX direction

### Navigation and page structure

- Keep a compact sidebar with Home, Dashboard, Questionnaire, Calculator, Recommendations, Progress, and Profile.
- Group account actions separately at the bottom of the sidebar; show the current account name and a sign-out control.
- On narrow screens, prioritize a collapsible navigation and a single-column content layout.
- Use consistent page titles, one-sentence descriptions, and a visible primary action per page.

### Visual system

- Retain the existing green, white, and light-neutral palette, with dark text and sufficient contrast.
- Use one type scale, spacing scale, button style, card radius, border treatment, and icon style across pages.
- Reserve saturated green for primary actions and meaningful positive states; do not use color alone to communicate status.
- Avoid decorative metric cards for values that are not defined or calculated.
- Keep charts simple, labeled, and paired with tables or text summaries.

### Accessibility and responsive behavior

- Check contrast for text, tags, chart labels, and disabled controls.
- Ensure keyboard users can reach every control and see focus indicators.
- Add descriptive labels and help text; avoid relying on placeholder text as the only label.
- Use plain language, readable font sizes, and short paragraphs.
- Test layouts at laptop, tablet, and phone widths; prevent charts and tables from requiring horizontal scrolling where practical.
- Provide non-color signals for selected, completed, invalid, and warning states.

### Common interaction states

Every data-backed page should define:

- **Loading:** explain what is being loaded if the operation is noticeable.
- **Empty:** explain why no data is shown and offer one next action.
- **Success:** confirm the saved item and provide a next step.
- **Validation error:** keep the user's values and point to the correction.
- **System error:** give a concise recovery action and avoid displaying raw exceptions or sensitive paths.

## 10. Functional requirements

- **FR1 — Account:** create an account with validated email and password; authenticate with a stored password hash; sign out; keep user-specific data isolated; communicate unsupported recovery for this prototype.
- **FR2 — Profile:** save and reload questionnaire responses by user; support editing without losing previous answers on validation errors.
- **FR3 — Calculator:** calculate annual transport fuel, electricity, and supported food emissions from documented factors; report water and waste separately unless reliable factors are added; persist the inputs, breakdown, factor version, and date needed to interpret the estimate.
- **FR4 — Estimate explanation:** show total, category values, units, factors, sources, limitations, and excluded categories alongside each result.
- **FR5 — Recommendation catalogue:** load stable action IDs, category, description, match terms, eligibility, effort/cost tiers, source, and review metadata; reject incomplete or invalid entries.
- **FR6 — Recommendation ranking:** use the current content-based method and eligibility rules; expose profile fit as a relevance score only; avoid quantified savings unless backed by a separate documented method.
- **FR7 — Goals:** add, update, pause, complete, and remove user-owned goals; prevent cross-user links; show the persisted state after rerun or sign-in.
- **FR8 — Dashboard:** display the latest saved estimate, category breakdown, goals, and saved recommendations; show useful empty states instead of placeholders.
- **FR9 — History:** compare only compatible estimates; identify changed factor versions or input scope before showing a trend.
- **FR10 — Data controls:** provide export and deletion flows with confirmation and safe handling of linked records.
- **FR11 — Navigation:** allow access to each page from a consistent navigation system; keep page selection stable across reruns and account changes.
- **FR12 — Feedback:** record optional action feedback without treating it as model ground truth until evaluated.

## 11. Non-functional requirements

- **Usability:** a first-time user should be able to reach a saved estimate and a recommendation without instructions from the developer.
- **Performance:** initial page and recommender should feel responsive for the current small local dataset; provide clear feedback if an operation takes more than a brief moment.
- **Reliability:** database operations should commit or roll back atomically; schema updates must preserve existing records.
- **Security:** use parameterized SQL, password hashing, generic login errors, input bounds, user-scoped queries, and no secrets in source control. Public deployment requires additional review and controls.
- **Privacy:** collect only necessary information, explain local storage, and support export/deletion before collecting real user-study data.
- **Accessibility:** usable keyboard navigation, sufficient contrast, descriptive labels, and charts with text/table alternatives.
- **Reproducibility:** version factor sets and recommendation catalogue data; evaluation should be repeatable from repository commands.
- **Transparency:** distinguish profile relevance, hypothetical scenarios, and measured progress; never imply that user-entered estimates are verified reductions.

## 12. Success measures and acceptance criteria

### Product measures

- Questionnaire completion rate and median completion time in a small consented usability test.
- Percentage of users who understand which categories are included in the estimate after viewing the result.
- Recommendation usefulness rating and percentage of users who save at least one action.
- Goal progress update and completion rates, interpreted as engagement rather than verified environmental impact.
- Number of catalogue actions with current source, applicability, and review metadata.

### Engineering acceptance criteria

- All DB CRUD and account isolation checks pass against a temporary database.
- Calculator outputs match independently hand-calculated reference profiles within a documented rounding tolerance.
- Existing recommender evaluation runs and reports ranking metrics without errors; results are described as scenario-label evaluation, not population truth.
- Users can register, sign in, navigate all pages, save a profile, calculate/save an estimate, save a goal, and see the saved state after rerun.
- Dashboard and progress contain no fabricated personal metrics; empty states appear when the user has no saved data.
- Keyboard and narrow-screen checks cover the primary user journey.
- No page shows raw stack traces, SQL, or file paths for routine user-facing errors.

## 13. Data and calculation policy

- Every factor must record a stable ID, value, unit, source, source URL, geography, reference year, and known limitations.
- Keep source factors and transformations documented; record a factor-set version on every saved estimate.
- Do not combine categories into one total if the system boundaries are materially incompatible without clearly labeling the total as partial and mixed-boundary.
- Keep water use and waste mass as non-GHG indicators until suitable locally matched factors and disposal-path inputs are available.
- Action savings require a separate documented calculation method and explicit baseline/behavior assumptions. Catalogue impact tiers alone are not numeric savings.
- Recommender evaluation labels should be reviewed and expanded; report sample size and evaluation limits with metrics.

## 14. Delivery roadmap

### Phase 1 — Trustworthy core and UI polish

- Fix questionnaire/calculator handoff and persistence of calculator activity inputs.
- Improve account/session handling, sign out, legacy-account messaging, and user-facing errors.
- Implement responsive page layouts, shared components, empty/loading/success states, and accessibility checks.
- Validate calculations with hand-calculated cases and add repeatable tests.

### Phase 2 — Useful personalization and history

- Improve action cards, category filters, alternatives, and user feedback.
- Compare compatible estimates and show factor/input changes clearly.
- Add goal target dates, check-ins, export, and data deletion.
- Run a small consented usability study with students; revise language and flows from findings.

### Phase 3 — Evidence-based expansion

- Research additional regional activity factors and action savings.
- Add categories only after documenting factors and input requirements.
- Consider localization, reminders, and grounded AI explanations if they have clear value and safe implementation plans.

## 15. Out of scope for the near-term mini project

- Automated purchasing, offsets, or carbon-neutrality claims.
- Social leaderboards or public sharing by default.
- Bank, utility, transport, or shopping account integrations.
- Predictive impact claims derived only from the content recommender.
- A public multi-tenant deployment without a separate security, privacy, and operations review.

## 16. Key risks and mitigations

| Risk | Mitigation |
|---|---|
| Partial or geographically mismatched factors produce misleading totals | Label scope, factor geography/year, and excluded categories next to estimates |
| Repeated or inconsistent activity inputs confuse users | Prefill supported profile values, identify their source, and let users edit them |
| Recommendation fit is misread as impact or confidence | Label the score as profile relevance and do not present unsupported savings |
| Trend compares unlike estimates | Compare only compatible scope/factor versions and annotate differences |
| Personal data is exposed or stranded | User-scoped queries, password hashes, export/delete, backups, and clear prototype security limits |
| Too much scope for a mini project | Deliver P0 first; defer optional AI, regional expansion, and reminders until the core is evaluated |

## 17. Open decisions

1. Which authoritative sources and update schedule should govern each future factor set?
2. Should first use start in guest/demo mode or require account creation before saving?
3. What exact activity inputs can be safely prefilled from the questionnaire without unsupported assumptions?
4. Which categories have enough India-relevant data to expand next?
5. Which screen sizes and language requirements are expected for the project demonstration?
6. Is report export required for the academic evaluation, and should it be PDF, CSV, or both?
