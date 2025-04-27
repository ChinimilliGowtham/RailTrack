Railway Management System 🚂

A Django-based web application designed to enhance railway travel by providing real-time train tracking, crowd density estimation, and coach layout visualization. Built with Python, Django, and the Indian Railway API, this project offers a seamless experience for passengers and railway enthusiasts.
   
About the Project
The Railway Management System is a web app that empowers users with real-time railway information. Whether you're planning a trip or managing station operations, this tool simplifies the process by offering insights into train schedules, crowd levels, and coach layouts. It’s built for scalability and user-friendliness, making railway travel more efficient and enjoyable.


Unique Features ✨

Real-Time Train Status: Track any train (e.g., "17644") and get its current station (e.g., "GDV") instantly.  
Crowd Density Estimation: Predicts station crowding within a ±15-minute window, helping you avoid peak hours.  
Coach Layout Visualization: View detailed coach layouts for any train number, making boarding easier.  
Filtered Train Schedules: See trains arriving at a station within a 45-minute window, perfect for quick planning.  
Recent Trains Tracking: Automatically saves and displays the last 5 trains you’ve viewed for quick access.

Getting Started 🛠️
Prerequisites

🐍 Python 3.8+
🌐 Django 5.2
📂 Git

Installation

Clone the Repository:
git clone https://github.com/ChinimilliGowtham/Railway-Management-System.git
cd Railway-Management-System


Set Up a Virtual Environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install Dependencies:
pip install -r requirements.txt


Run Migrations:
python manage.py migrate


Start the Development Server:
python manage.py runserver

Open your browser and navigate to http://127.0.0.1:8000 to explore the app!


Connecting API Keys 🔑
This project uses the Indian Railway API to fetch live train data. Follow these steps to set up your API key:

Sign Up on RapidAPI and Indian Rail API:

I used the RapidAPI for live tracking the train 
Visit RapidAPI's Indian Railway API to get your API key.
Link: https://rapidapi.com/rahilkhan224/api/indian-railway-irctc
Create an account or log in, then subscribe to the Indian Railway API (free tier available).

And i used the Indian Railway API key for coach_layout,crowd_density and trains_at_station
Visit the follwing link and sign up to get the API
Link: https://indianrailapi.com/api-collection
Create an account or log in, then subscribe to the Indian Railway API (free tier available).

NOTE:I am also using the Free tier APIs.

Add Your API Key:

Create a .env file in the project root:echo "CROWD_API=your_api_key_here" > .env
echo "LIVE_TRACK_API=your_api_key_here" >> .env


Replace your_api_key_here with the key you obtained from RapidAPI.


Secure Your Key:

The .gitignore already excludes .env, ensuring your API key stays private.



Usage 🎯

🚆 Track a Train: Enter a train number (e.g., "17644") to see its live status.  
📊 Check Crowd Density: Input a station code (e.g., "MAS") to estimate crowd levels.  
🛤️ View Coach Layout: Provide a train number to visualize its coach positions.  
⏰ Explore Schedules: Filter trains at a station within a 45-minute window.

Demo 
![image](https://github.com/user-attachments/assets/6a6fe7aa-6a3a-41b1-9bc5-b1b3b3b1f202)


Contributing 🤝
Contributions are welcome! Fork the repo, make your changes, and submit a pull request. For major updates, please open an issue first to discuss your ideas.

Contact 📬
Have questions? Reach out via GitHub Issues or connect with me on LinkedIn.
LinkedIn profile: https://www.linkedin.com/in/gowtham-chinimilli-933391296/

Happy tracking! 🚉
