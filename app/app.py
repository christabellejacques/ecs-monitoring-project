#Flask is a python libration that lets you build web applications.
#It's like a template that handles "when someone visits this URL, do this"

from flask import Flask, jsonify
import logging

#Create a Flask application
app = Flask(__name__)

#Set up logging to see what is happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#Route 1: The health check endpoint
#This is what ECS will ask: "Is this container healthy?"
#Return a response in JSON format 
@app.route('/health', methods=['GET']) 

#This endpoint returns whether the application is healthy.
#ECS will call this every 5 seconds to check if your app is alive.
def health_check(): 
    logger.info("Health check requested")
    return jsonify({"status": "healthy",
                    "message": "The application is running smoothly!"
                    }), 200  # 200 = "everything is fine"

#Route 2: The actual application endpoint
@app.route('/api/message', methods=['GET'])
#A simple endpoint that returns a message.
#This is what users would actually call.

def get_message():
    logger.info("Message endpoint called")
    return jsonify({
        'message': 'Hello from ECS!',
        'timestamp': '2026-05-02'
    }), 200

#Route 3: For testing - this will make the app crash to test ECS's health check
@app.route('/simulate-failure', methods=['POST'])

#When you call this, the health check will start failing.
#This simulates a real production failure.

def simulate_failure():
    logger.warning("Simulating failure as requested")
    raise Exception("Simulated failure for testing ECS health checks")

#Run the application
if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(host='0.0.0.0', port=5000, debug=False)  # Listen on all interfaces, port 5001, and turn off debug mode for production