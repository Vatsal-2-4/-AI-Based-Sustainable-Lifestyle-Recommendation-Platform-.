# Tests

Run the application smoke and unit tests from the project root:

```bash
python -m unittest discover -s tests -v
```

The suite uses temporary SQLite databases and covers:

- Password hashing, authentication, validation, CRUD persistence, and schema migration.
- Footprint annualization, input rejection, and separate water/waste indicators.
- Recommendation ranking, matched-habit explanations, and eligibility filters.
- Account-only SQLite backups, password-hash omission, and demo-only reset behavior.

The tests do not use the application's local database file or delete user records.
