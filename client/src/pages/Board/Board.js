import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import FarpointSidebar from "../../components/FarpointSidebar/FarpointSidebar";
import "./Board.css";

const Board = () => {
  const navigate = useNavigate();
  const [isPopupOpen, setIsPopupOpen] = useState(false);
  const [selectedSummary, setSelectedSummary] = useState("");
  const [previousInterviews, setPreviousInterviews] = useState([]);
  const [upcomingInterviews, setUpcomingInterviews] = useState([]);
  const apiUrl = process.env.REACT_APP_API_URL;

  const fetchCalendarEvents = async (navigate) => {
    try {
      const response = await fetch(`${apiUrl}/board/get_calendar_events`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        // Handle both unauthorized and internal server error responses
        if (response.status === 401 || response.status === 500) {
          localStorage.removeItem("access_token"); // Remove the token for security
          navigate("/login"); // Redirect to login page for re-authentication
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      let idCounter = 1; // Initialize counter for ID
      const filteredAndLimitedEvents = data.events
        .filter(
          (event) =>
            event.attendees &&
            event.attendees.length > 0 && // Ensure there are attendees
            event.attendees.some(
              (attendee) => attendee.email && attendee.email.trim() !== ""
            ) // Ensure at least one attendee has a non-empty email
        )
        .slice(0, 6); // Select up to the first 6 events

      setUpcomingInterviews(
        filteredAndLimitedEvents.map((event) => {
          return {
            id: idCounter++, // Increment ID for each event
            summary: event.summary || "N/A",
            attendees: event.attendees
              ? event.attendees.map((attendee) => attendee.email).join(", ")
              : "N/A",
            link:
              (event.conferenceData &&
                event.conferenceData.entryPoints &&
                event.conferenceData.entryPoints[0].uri) ||
              "N/A",
            date: new Date(event.start.dateTime).toLocaleDateString(),
            startTime: new Date(event.start.dateTime).toLocaleTimeString(),
          };
        })
      );
    } catch (error) {
      console.error("Error fetching calendar events:", error);
      // Optionally, handle additional error logic here if needed
    }
  };

  const fetchPreviousInterviews = async () => {
    try {
      const response = await fetch(`${apiUrl}/board/previous_interviews`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        if (response.status === 422) {
          navigate("/login");
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setPreviousInterviews(data.previousInterviews); // Update state with fetched data
    } catch (error) {
      console.error("Error fetching previous interviews:", error);
    }
  };

  useEffect(() => {
    fetchPreviousInterviews();
    fetchCalendarEvents();
  }, []);

  const handleStartNewInterview = () => {
    // Define the action to be performed on button click
    // For example, navigate to a new interview setup page
    navigate("/InterviewBoard");
  };

  const MeetingSummaryPopup = ({ isOpen, onClose, summary }) => {
    if (!isOpen) return null;

    return (
      <div className="modal-overlay">
        <div className="modal-container">
          <button className="modal-close-btn" onClick={onClose}>
            X
          </button>
          <div className="modal-content">
            <p>{summary}</p>
          </div>
        </div>
      </div>
    );
  };

  const handleCardClick = (id) => {
    // Find the clicked interview from the previousInterviews array
    const clickedInterview = previousInterviews.find(
      (interview) => interview.id === id
    );

    // Check if the interview exists
    if (clickedInterview) {
      // Use React Router's `navigate` to go to the ArchivedMeeting page with the `meeting_id`
      navigate(`/archived-meeting/${clickedInterview.id}`);
    } else {
      console.error("Interview not found.");
    }
  };

  const handleClosePopup = () => {
    setIsPopupOpen(false);
    setSelectedSummary("");
  };

  return (
    <div className="board-container">
      <FarpointSidebar />
      <div className="board-content">
        <div className="interviews-container">
          <div className="upcoming-interviews-header">
            <h2>Upcoming Meetings</h2>
            <button
              className="start-new-interview-btn"
              onClick={handleStartNewInterview}
            >
              Start New Meeting
            </button>
          </div>

          <div className="interviews">
            {upcomingInterviews.map((interview) => (
              <div
                key={interview.id}
                className="interview-card"
                onClick={() => window.open(interview.link, "_blank")}
              >
                <h3>{interview.summary}</h3>
                {interview.attendees !== "N/A" && (
                  <p>Attendees: {interview.attendees}</p>
                )}
                <p>
                  <a
                    href={interview.link}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Join Meeting
                  </a>
                </p>
                <p>Date: {interview.date}</p>
                <p>Start Time: {interview.startTime}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="interviews-container">
          <h2>Previous Meetings</h2>
          <div className="interviews">
            {previousInterviews.map((interview) => (
              <div
                key={interview.id}
                className="interview-card"
                onClick={() => handleCardClick(interview.id)}
              >
                <h3>{interview.company}</h3>
                <p>{interview.attendees}</p>
                <p>{interview.description}</p>
                <p>{interview.date}</p>
                <p>{interview.startTime}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
      <MeetingSummaryPopup
        isOpen={isPopupOpen}
        onClose={handleClosePopup}
        summary={selectedSummary}
      />
    </div>
  );
};

export default Board;
