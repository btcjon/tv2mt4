# Refactor Flask Application

Use `app_old.py` as the original app code for reference. Do not edit, but use code from there to complete the following tasks. I will provide all needed files and code. Feel free to make new files and code as needed.  keep this refactor.md file updated with concise notes and task status.

## Task Status
Each task is prepended with its current status. There are only 3 statuses allowed:
- Done: Task is complete
- Incomplete: Task is not fully complete or unsure
- Verified: Task has been verified with testing or code runs as expected

## Method of completion: Think and make edits in a step-by-step manner. Do not try to do multiple tasks at once. Do one think at a time and do not move onto next until you are certain the step is complete as it can be.

## Tasks

1. **Flask App Setup** (File: `app.py`)
    - Done: Make new blank `app.py` file
    - Incomplete: Keep only the Flask app initialization, configuration, and `if __name__ == "__main__":` block in this file. Ensure Flask app (`Flask(__name__)`) and global configurations are defined here. `if __name__ == "__main__":` should contain only the `app.run()` call with necessary parameters.

2. **Logging Configuration** (File: `logger.py`)
    - Done: Create a file named `logger.py`.
    - Incomplete: Move all logging setup code (handler creation, level setting, formatter definition) to this file. Define a function, e.g., `setup_logger()`, to configure and return a logger instance. Import and use this function in `app.py` and other modules as needed.

3. **AirtableOperations Class** (File: `airtable_operations.py`)
    - Done: Create a file named `airtable_operations.py`.
    - Done: Move the `AirtableOperations` class with all its methods to this file.
    - Incomplete: Include all necessary imports in this file. Import `AirtableOperations` in `app.py` for instantiation and use.

4. **Webhook Handlers** (File: `webhook_handlers.py`)
    - Done: Create a file named `webhook_handlers.py`.
    - Done: Transfer webhook request handling logic from `app.py` to this file.
    - Incomplete: Include request parsing, decision-making, and response generation. Define separate functions for each logical part. Import and use these functions in Flask routes in `app.py`.

5. **Utility Functions** (File: `utils.py`)
    - Done: Create a file named `utils.py`.
    - Incomplete: Move utility functions like `send_pineconnector_command` to this file. Ensure all dependencies and imports are included. Import these utilities where needed (e.g., `app.py`, `webhook_handlers.py`).

## Additional Notes
- Test each component post-restructuring to ensure functionality is intact.
- Update any impacted relative imports.
- Adhere to clear and consistent coding standards throughout the refactoring.
- Document your code for better understanding and maintainability.