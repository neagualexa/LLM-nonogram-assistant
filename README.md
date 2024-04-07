# Final Year Project - user- & task-tailored AI assistant

This repository contains the resourses to set up the AI assistant that helps the user during their progress on completing Nonograms.
This is a Flask application that serves as a chatroom with AI-featured puzzle checking and hinting functionalities.

This is one of the repos for the Final Year Project of [Alexandra Neagu (@neagualexa)](https://github.com/neagualexa) titled `XXX` at Imperial College London.

The repository containing the Nonogram Game Interface developed in `Unity`, is found at [NonogramUnity](https://github.com/neagualexa/NonogramUnity).

## Routes

The application has the following routes:

- `/`: The home page of the chatroom application.
- `/send_message`: This route is used to send a message to converse with the Language Model.
- `/check_puzzle_meaning`: This route is used to check the meaning of a puzzle.
- `/check_puzzle_progress`: This route is used to check the progress of a puzzle and allow an LLM to generate a progress-tailored hint to help the user.
- `/clear_history`: This route is used to clear the chat history.

## Setup

1. Clone the repository:
    ```
    git clone <repository_url>
    ```

2. Navigate into the cloned repository:
    ```
    cd <repository_name>
    ```

3. Install the required packages:
    ```
    pip install -r requirements.txt
    ```

4. Run the application:
    ```
    python3 app.py
    ```

## Usage

To use the application, navigate to `localhost:5000` in your web browser.


