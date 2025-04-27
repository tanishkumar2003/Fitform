import json
from datetime import datetime
import uuid
import statistics
import time

class ExerciseSession:
    def __init__(self, user_context=None, equipment=None):
        self.session_data = {
            "sessionId": str(uuid.uuid4()),
            "dateTime": datetime.utcnow().isoformat(),
            "exercise": "Bicep Curl",
            "userContext": user_context or {
                "goal": "Technique Improvement",
                "experienceLevel": "Beginner",
                "notes": None
            },
            "equipment": equipment or {
                "type": "Dumbbells",
                "weight": 0,
                "unit": "lbs"
            },
            "warmupPerformed": False,
            "sets": [],
            "sessionSummary": {
                "totalVolume": 0,
                "totalReps": 0,
                "averageRPE": 0,
                "primaryFeedbackArea": None,
                "overallFeeling": None,
                "trainerNotes": None,
                "timeUnderTension": 0,
                "averageRepDuration": 0,
                "formIssues": []
            }
        }
        self.current_set = 1
        self.last_set_time = None
        self.rep_data = []
        self.set_start_time = None
        self.start_time = time.time()

    def start_set(self):
        """Initialize a new set"""
        self.rep_data = []
        self.set_start_time = time.time()
        self.last_rep_time = None

    def add_rep_data(self, metrics):
        """Add data for a single rep with timing information"""
        current_time = time.time()
        
        # Check if metrics is already in the expected format with repNumber, timestamp, metrics, timing
        if isinstance(metrics, dict) and "repNumber" in metrics and "metrics" in metrics:
            # It's already properly formatted
            self.rep_data.append(metrics)
            self.last_rep_time = current_time
            return
        
        # If it's not in the expected format, try to construct one
        try:
            # Construct simplified version from real-time metrics
            form_metrics = metrics.get('form_metrics', {})
            rep_metrics = {
                "repNumber": len(self.rep_data) + 1,
                "timestamp": current_time,
                "metrics": {
                    "elbow_flare": form_metrics.get('elbow_flare', 0),
                    "torso_lean": form_metrics.get('torso_lean', 0),
                    "shoulder_elevation": form_metrics.get('shoulder_elevation', 0),
                    "rom_percentage": form_metrics.get('rom_percentage', 0),
                },
                "timing": {
                    "duration": 0,  # No timing info available
                    "time_since_last_rep": current_time - self.last_rep_time if self.last_rep_time else 0,
                    "time_in_set": current_time - self.set_start_time if self.set_start_time else 0
                }
            }
            
            # Add timing metadata to the metrics
            metrics.update({
                "timestamp": current_time,
                "timeInSet": current_time - self.set_start_time if self.set_start_time else 0,
                "timeInSession": current_time - self.start_time,
                "timeSinceLastRep": current_time - self.last_rep_time if self.last_rep_time else 0
            })
            
            self.rep_data.append(rep_metrics)
            self.last_rep_time = current_time
        except Exception as e:
            # Log error but don't crash
            print(f"Error adding rep data: {e}")

    def end_set(self, subjective_feedback=None):
        """End current set and calculate metrics"""
        if not self.rep_data:
            return

        # Update weight if changed
        if subjective_feedback and 'weight' in subjective_feedback:
            self.session_data["equipment"]["weight"] = subjective_feedback["weight"]

        # Calculate rest period
        rest_period = None
        if self.last_set_time:
            rest_period = int(self.set_start_time - self.last_set_time)

        # Calculate objective metrics
        avg_metrics = self._calculate_set_metrics()
        
        # Prepare set data
        set_data = {
            "setNumber": self.current_set,
            "weight": self.session_data["equipment"]["weight"],
            "targetReps": 10,
            "actualReps": len(self.rep_data),
            "restPeriodBeforeSet": rest_period,
            "timeUnderTension": time.time() - self.set_start_time,
            "objectiveMetrics": avg_metrics,
            "subjectiveFeedback": subjective_feedback or self._default_feedback(),
            "repsData": self.rep_data  # Store individual rep data
        }

        self.session_data["sets"].append(set_data)
        self.current_set += 1
        self.last_set_time = time.time()

    def _calculate_set_metrics(self):
        """Calculate averaged and max metrics for the set"""
        if not self.rep_data:
            return {}

        def safe_avg(values):
            return statistics.mean(values) if values else 0

        def safe_max(values):
            return max(values) if values else 0

        try:
            # Extract metrics from rep data
            elbow_flares = []
            torso_leans = []
            rom_percentages = []
            
            for rep in self.rep_data:
                if "metrics" in rep:
                    metrics = rep["metrics"]
                    if "elbow_flare" in metrics:
                        elbow_flares.append(metrics["elbow_flare"])
                    if "torso_lean" in metrics:
                        torso_leans.append(metrics["torso_lean"])
                    if "rom_percentage" in metrics:
                        rom_percentages.append(metrics["rom_percentage"])
            
            # Calculate timing data if available
            rep_durations = []
            inter_rep_times = []
            for rep in self.rep_data:
                if "timing" in rep:
                    timing = rep["timing"]
                    if "duration" in timing:
                        rep_durations.append(timing["duration"])
                    if "time_since_last_rep" in timing:
                        inter_rep_times.append(timing["time_since_last_rep"])
            
            return {
                "avgElbowFlareOut": round(safe_avg(elbow_flares), 2),
                "maxElbowFlareOut": round(safe_max(elbow_flares), 2) if elbow_flares else 0,
                "avgTorsoLean": round(safe_avg(torso_leans), 2),
                "maxTorsoLean": round(safe_max(torso_leans), 2) if torso_leans else 0,
                "avgROMPercentage": round(safe_avg(rom_percentages), 2),
                "minROMPercentage": round(min(rom_percentages), 2) if rom_percentages else 0,
                "repTimings": {
                    "avgRepDuration": round(safe_avg(rep_durations), 2) if rep_durations else 0,
                    "avgTimeBetweenReps": round(safe_avg(inter_rep_times), 2) if inter_rep_times else 0
                }
            }
        except Exception as e:
            # Return empty metrics on error
            print(f"Error calculating set metrics: {e}")
            return {
                "avgElbowFlareOut": 0,
                "maxElbowFlareOut": 0,
                "avgTorsoLean": 0,
                "maxTorsoLean": 0,
                "avgROMPercentage": 0,
                "minROMPercentage": 0,
                "repTimings": {
                    "avgRepDuration": 0,
                    "avgTimeBetweenReps": 0
                }
            }

    def _default_feedback(self):
        """Generate default subjective feedback structure"""
        return {
            "rpe": 0.0,
            "rir": 0,
            "fatiguePointReason": None,
            "muscleFeelFocus": "Biceps",
            "painFlag": False,
            "painLocation": None,
            "notes": None
        }

    def update_notes(self, notes):
        """Update session notes"""
        self.session_data["userContext"]["notes"] = notes

    def add_session_summary(self, summary):
        """Add or update session summary data"""
        if summary:
            self.session_data["sessionSummary"].update(summary)

    def save_session(self):
        """Save session data to file with calculated totals"""
        # Calculate final session metrics
        total_reps = sum(set_data["actualReps"] for set_data in self.session_data["sets"])
        total_volume = total_reps * self.session_data["equipment"]["weight"]
        
        self.session_data["sessionSummary"].update({
            "totalReps": total_reps,
            "totalVolume": total_volume,
            "sessionDuration": time.time() - self.start_time,
            "averageRPE": self._calculate_average_rpe()
        })

        filename = f"session_{self.session_data['sessionId']}.json"
        with open(filename, 'w') as f:
            json.dump(self.session_data, f, indent=2)
        return filename

    def _calculate_average_rpe(self):
        """Calculate average RPE across all sets"""
        rpes = [set_data["subjectiveFeedback"]["rpe"]
                for set_data in self.session_data["sets"] 
                if set_data["subjectiveFeedback"]["rpe"] is not None]
        return round(statistics.mean(rpes), 1) if rpes else None
