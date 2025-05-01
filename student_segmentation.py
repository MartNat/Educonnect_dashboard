import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
import joblib
import os

# Update the create_training_data function with more diverse courses
def create_training_data():
    np.random.seed(42)
    n_samples = 1000
    
    # Update source options to match form options exactly
    sources = ['walk-in', 'fairs', 'school visit', 'referrals']
    destinations = ['UK', 'US', 'Australia', 'Canada', 'New Zealand', 'Ireland']
    levels = ['undergraduate', 'postgraduate']
    # Add more course categories for broader coverage
    courses = ['Business', 'Engineering', 'Medicine', 'Arts', 'Science', 'Computer', 
              'Law', 'Economics', 'Mathematics', 'Psychology', 'Other']
    
    data = {
        'source': np.random.choice(sources, n_samples),
        'email_responses': np.random.randint(0, 10, n_samples),
        'call_responses': np.random.randint(0, 10, n_samples),
        'destination': np.random.choice(destinations, n_samples),
        'level_of_study': np.random.choice(levels, n_samples),
        'course_category': np.random.choice(courses, n_samples),
    }
    
    # Create conversion probability based on features
    conversion_prob = []
    for i in range(n_samples):
        score = 0
        # Source weight - updated weights
        source_weights = {
            'referrals': 0.8, 
            'walk-in': 0.6, 
            'fairs': 0.5, 
            'school visit': 0.4
        }
        score += source_weights[data['source'][i]]
        
        # Response engagement weight
        engagement = (data['email_responses'][i] + data['call_responses'][i]) / 20
        score += engagement
        
        # Destination weight
        destination_weights = {'UK': 0.7, 'US': 0.8, 'Australia': 0.6, 
                             'Canada': 0.7, 'New Zealand': 0.5, 'Ireland': 0.6}
        score += destination_weights[data['destination'][i]]
        
        # Add some randomness
        score = score / 3 + np.random.normal(0, 0.1)
        conversion_prob.append(1 if score > 0.6 else 0)
    
    data['converted'] = conversion_prob
    return pd.DataFrame(data)

def save_model(model, encoders, directory='static/models'):
    """Save the model and encoders to disk"""
    os.makedirs(directory, exist_ok=True)
    joblib.dump(model, os.path.join(directory, 'rf_model.pkl'))
    joblib.dump(encoders, os.path.join(directory, 'encoders.pkl'))
    print(f"Model and encoders saved to {directory}")

def load_model(directory='static/models'):
    """Load the model and encoders from disk"""
    model_path = os.path.join(directory, 'rf_model.pkl')
    encoders_path = os.path.join(directory, 'encoders.pkl')
    
    if os.path.exists(model_path) and os.path.exists(encoders_path):
        model = joblib.load(model_path)
        encoders = joblib.load(encoders_path)
        print("Model and encoders loaded successfully")
        return model, encoders
    else:
        print("No saved model found. Training new model...")
        model, encoders = train_model()
        save_model(model, encoders, directory)
        return model, encoders

# Modify the train_model function to save the model
def train_model():
    # Create dataset
    df = create_training_data()
    
    # Create separate encoders for each categorical feature
    source_encoder = LabelEncoder()
    destination_encoder = LabelEncoder()
    level_encoder = LabelEncoder()
    course_encoder = LabelEncoder()
    
    # Prepare features with separate encoders
    X = pd.DataFrame({
        'source': source_encoder.fit_transform(df['source']),
        'email_responses': df['email_responses'],
        'call_responses': df['call_responses'],
        'destination': destination_encoder.fit_transform(df['destination']),
        'level_of_study': level_encoder.fit_transform(df['level_of_study']),
        'course_category': course_encoder.fit_transform(df['course_category'])
    })
    
    y = df['converted']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train model
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    
    # Print model performance
    print("Model Performance:")
    print(classification_report(y_test, rf_model.predict(X_test)))
    
    # Save all encoders in a dictionary
    encoders = {
        'source': source_encoder,
        'destination': destination_encoder,
        'level': level_encoder,
        'course': course_encoder
    }
    
    save_model(rf_model, encoders)
    return rf_model, encoders

def calculate_initial_probability(student_data):
    """Calculate initial conversion probability for a new student based on their profile"""
    base_probability = 30  # Base probability starts at 30%
    
    # Source/Lead Type bonus
    source_bonus = {
        'referrals': 15,    # Highest conversion rate
        'school visit': 10,  # Direct engagement
        'fairs': 8,         # Active interest
        'walk-in': 5        # General inquiry
    }.get(student_data['source'].lower(), 0)
    
    # Study Level bonus
    level_bonus = 10 if student_data['level_of_study'].lower() == 'postgraduate' else 5
    
    # Destination/Country bonus
    destination_bonus = {
        'UK': 5,       # Fastest processing
        'Canada': 4,   # Good acceptance rate
        'Australia': 3,# Moderate processing
        'US': 2        # Longer processing
    }.get(student_data['destination'].upper(), 0)
    
    # Calculate total probability
    total_probability = base_probability + source_bonus + level_bonus + destination_bonus
    
    # Cap at 100%
    return min(round(total_probability), 100)

def predict_conversion(student_data, model, encoders):
    """Predict conversion probability for a single student"""
    try:
        # Extract course category, default to 'Other' if not in known categories
        course_category = student_data['course_of_study'].split()[0]
        if course_category not in encoders['course'].classes_:
            course_category = 'Other'
        
        features = pd.DataFrame({
            'source': [encoders['source'].transform([student_data['source']])[0]],
            'email_responses': [student_data['email_responses']],
            'call_responses': [student_data['call_responses']],
            'destination': [encoders['destination'].transform([student_data['destination']])[0]],
            'level_of_study': [encoders['level'].transform([student_data['level_of_study']])[0]],
            'course_category': [encoders['course'].transform([course_category])[0]]
        })
        
        probability = model.predict_proba(features)[0][1]
        return round(probability * 100, 2)
    except Exception as e:
        print(f"Error in prediction for course {student_data['course_of_study']}: {e}")
        # Return a moderate probability if prediction fails
        return 50

if __name__ == "__main__":
    # Train and save the model
    model, encoder = train_model()