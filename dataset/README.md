# Project datasets

## `actions.csv`

The catalogue contains curated actions based on public guidance from India's Mission LiFE initiative, with an energy-efficiency action linked to the Bureau of Energy Efficiency. It is a content dataset, not a set of measured user preferences. It intentionally does not contain fabricated kg CO2e savings.

| Field | Meaning |
|---|---|
| `action_id` | Stable ID used by the app, evaluation labels, and database |
| `category` | One of six lifestyle categories |
| `title`, `description` | Text displayed to the user and included in the item document |
| `match_terms` | Related words and habits that help TF-IDF match a profile to an action |
| `eligibility` | Rule key for removing actions that cannot apply to a profile |
| `impact_tier` | Qualitative catalogue priority (low/medium/high), not a numeric saving |
| `cost_tier` | Approximate implementation-cost tier used for tie-breaking |
| `difficulty` | Relative effort, 1 (easiest) to 5 (hardest) |
| `source_name`, `source_url` | Guidance reference for the action |

## `emission_factors.csv` and `food_emission_factors.csv`

These files contain factor values and source/version/scope metadata used by the calculator. Electricity uses CEA FY 2023-24. Transport uses IPCC default combustion factors with default net calorific values and fuel densities. Food uses global mean product factors from Poore and Nemecek, processed by Our World in Data. These factors have different boundaries and food is not India-specific. Water and waste currently have no CO2e factors in the calculator; their annual physical quantities are shown separately. The recommendation model does not use these emission factors.

## `evaluation_profiles.csv`

Small, manually labeled test scenarios. `expected_action_ids` lists catalogue actions considered relevant by the project team for that scenario. These labels are useful for a reproducible classroom evaluation, but they are not user-study ground truth. Add scenarios and review labels with evaluators before drawing broad conclusions.
