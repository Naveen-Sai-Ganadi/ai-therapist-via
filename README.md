

# Telegram AI Therapist Bot

This project is a Telegram bot designed to act as an AI therapist, providing supportive and empathetic responses to users. The bot leverages the Groq API for generating responses and is deployed using Docker. The setup ensures continuous operation by using Render's background worker service.

## Features

- Provides empathetic and supportive responses to user messages.
- Uses the Groq API for natural language generation.
- Continuously runs on Render's background worker service.
- Includes custom keyboard buttons for easy user interaction.
- Commands for starting a new conversation and resetting conversation history.

## Project Structure

- `telegram_bot.py`: Main script for the Telegram bot.
- `groq_response.py`: Script for handling responses from the Groq API.
- `requirements.txt`: List of Python dependencies.
- `Dockerfile`: Instructions for building the Docker image.
- `docker-compose.yml`: Docker Compose configuration file.

## Getting Started

### Prerequisites

- Docker
- Docker Compose
- A Telegram bot token from BotFather
- Groq API key

### Installation

1. **Clone the repository**:
   ```sh
   git clone https://github.com/yourusername/telegram-ai-therapist-bot.git
   cd telegram-ai-therapist-bot
   ```

2. **Set up environment variables**:
   Create a `.env` file in the root directory and add your Telegram bot token and Groq API key:
   ```env
   TELEGRAM_BOT_API_TOKEN=your-telegram-bot-token
   GROQ_API_KEY=your-groq-api-key
   ```

3. **Build and run with Docker Compose**:
   ```sh
   docker-compose up --build
   ```

## Deployment

### Deploy on Render

1. **Push your code to GitHub**:
   ```sh
   git add .
   git commit -m "Deploy Telegram bot to Render"
   git push origin main
   ```

2. **Deploy on Render**:
   - Log in to your Render account.
   - Click on "New" and select "Web Service".
   - Connect your GitHub repository.
   - Choose the repository that contains your Telegram bot project.
   - Select "Docker" for the environment.
   - Configure the service:
     - Set the build command to:
       ```sh
       docker build -t telegram_bot .
       ```
     - Set the start command to:
       ```sh
       docker run -p 8080:8080 telegram_bot
       ```
     - Add environment variables (TELEGRAM_BOT_API_TOKEN and GROQ_API_KEY).
   - Click on "Create Web Service" and wait for the deployment to complete.

3. **Create a Background Worker on Render**:
   - Go to your Render dashboard.
   - Click on "New" and select "Background Worker".
   - Connect it to the same GitHub repository.
   - Use the same Dockerfile.
   - Set the start command for the worker to:
     ```sh
     python telegram_bot.py
     ```
   - Add the necessary environment variables (TELEGRAM_BOT_API_TOKEN and GROQ_API_KEY).

## Usage

### Commands

- **/start**: Start a new conversation.
- **/reset**: Reset conversation history.
- **/help**: Get help information.

### Custom Keyboard

The bot provides a custom keyboard with the following options:
- Start a new conversation
- Delete your conversation history

## Access the Bot

You can access the bot on Telegram using the following link: [AI Therapist Bot](http://t.me/MyAICoachBot).

## Contributing

1. Fork the repository.
2. Create a new feature branch (`git checkout -b feature/new-feature`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/new-feature`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Telegram for their Bot API.
- Groq for their API used for generating responses.