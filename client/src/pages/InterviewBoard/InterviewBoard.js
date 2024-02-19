import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import FarpointSidebar from "../../components/FarpointSidebar/FarpointSidebar";

import "./InterviewBoard.css";

const InterviewBoard = () => {
  const statusRef = useRef(null);
  const transcriptRef = useRef(null);
  const socketRef = useRef(null);
  const audioCtx = useRef(null);
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const generateKeyNotesIntervalRef = useRef(null);
  const generateQuestionsIntervalRef = useRef(null);
  const [keyNotes, setKeyNotes] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(true);
  const [interviewName, setInterviewName] = useState("");
  const [interviewTitle, setInterviewTitle] = useState("");
  const [interviewCompanyName, setInterviewCompanyName] = useState("");
  const [interviewDate, setInterviewDate] = useState("");
  const [transcriptUpdated, setTranscriptUpdated] = useState(false);
  const [expandedQuestionId, setExpandedQuestionId] = useState(null);
  const [visibleAnswers, setVisibleAnswers] = useState({});
  const [companyDetails, setCompanyDetails] = useState("");
  const navigate = useNavigate();
  const token = localStorage.getItem("access_token");
  const apiUrl = process.env.REACT_APP_API_URL;
  const tranURL = process.env.REACT_APP_TRANSCRIPT_URL;
  const [isLoading, setIsLoading] = useState(false);

  const Modal = ({ isOpen, setIsModalOpen, onDetailsSubmit }) => {
    const [companyDetails, setCompanyDetails] = useState("");
    const [formData, setFormData] = useState({
      name: "",
      title: "",
      company: "",
      companywebsite: "",
      jobDescription: "",
      interviewObjective: "",
    });

    const handleInputChange = (event) => {
      const { name, value } = event.target;
      setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const fetchCompanyDetails = async () => {
      try {
        const response = await fetch(`${apiUrl}/interview/clientinfo`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ company: formData.company }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setCompanyDetails(data.details);
      } catch (error) {
        console.error("Error fetching company details:", error);
      }
    };

    const handleSubmit = async (event) => {
      event.preventDefault();

      const formData = new FormData(event.target);
      const data = {
        name: formData.get("name"),
        title: formData.get("title"),
        company_name: formData.get("company"),
        company_website: formData.get("companywebsite"),
        job_description: formData.get("jobDescription"),
        company_description: formData.get("aboutClient"),
        interview_description: formData.get("interviewObjective"),
        date: new Date().toISOString().split("T")[0],
        start_time: new Date().toTimeString().split(" ")[0],
        finish_time: "",
        finished: false,
        meeting_summary: "",
      };

      sessionStorage.setItem("interviewDetails", JSON.stringify(data));
      // Call a function to update state in parent component (InterviewBoard)
      onDetailsSubmit(data);

      try {
        const response = await fetch(`${apiUrl}/interview/add`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        });

        if (!response.ok) {
          if (response.status === 422) {
            // Navigate to login page only if response status is 422
            navigate("/login");
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const responseJson = await response.json();
        console.log("POST request response:", responseJson);

        // Store _id in sessionStorage
        if (responseJson && responseJson._id) {
          sessionStorage.setItem("interviewId", responseJson._id);
          setIsRecording(true); // Set recording state to true
          await startAudioStreamingAndTranscription();
        }
      } catch (error) {
        console.error("Error during POST request:", error);
      } finally {
        // Close modal in finally block to ensure it closes regardless of API success
        setIsModalOpen(false);
      }
    };

    if (!isOpen) return null;

    return (
      <div className="modal-overlay">
        <div className="modal-container">
          <button
            type="button"
            onClick={() => {
              setIsModalOpen(false); // Close the modal
              navigate("/Board"); // Navigate to the Board route
            }}
            className="close-btn"
          >
            &times;
          </button>
          <h2>Meeting Details</h2>
          <form className="modal-form" onSubmit={handleSubmit}>
            <input
              type="text"
              name="name"
              placeholder="Name"
              required
              value={formData.name}
              onChange={handleInputChange}
            />
            <input
              type="text"
              name="title"
              placeholder="Title"
              required
              value={formData.title}
              onChange={handleInputChange}
            />
            <input
              type="text"
              name="company"
              placeholder="Company"
              required
              value={formData.company}
              onChange={handleInputChange}
            />
            <input
              type="text"
              name="companywebsite"
              placeholder="Company Website"
              required
              value={formData.companywebsite}
              onChange={handleInputChange}
            />
            <textarea
              name="jobDescription"
              placeholder="Job Description"
              rows="3"
              required
              value={formData.jobDescription}
              onChange={handleInputChange}
            ></textarea>
            <label htmlFor="interviewObjective">Meeting Objective:</label>
            <select
              name="interviewObjective"
              id="interviewObjective"
              required
              value={formData.interviewObjective}
              onChange={handleInputChange}
            >
              <option value="">Select Objective</option>
              <option value="kickoff">Kickoff</option>
              <option value="head of department interview">
                Head of Department Interview
              </option>
              <option value="management interview">Management Interview</option>
              <option value="on the ground interview">
                On the Ground Interview
              </option>
              <option value="status update">Status Update</option>
              <option value="Data Integrity Interview">
                Data Integrity Interview
              </option>
            </select>
            <button type="button" onClick={fetchCompanyDetails}>
              Retrieve Company Information
            </button>
            <textarea
              name="aboutClient"
              placeholder="About the Client (Optional)"
              rows="8"
              value={companyDetails || formData.aboutClient}
              onChange={handleInputChange}
            ></textarea>
            <button type="submit">Submit</button>
          </form>
        </div>
      </div>
    );
  };

  // Function for audio streaming and transcription logic
  const startAudioStreamingAndTranscription = async () => {
    // Ensure that the interview ID is obtained before starting
    const interviewId = sessionStorage.getItem("interviewId");
    if (!interviewId) {
      console.error(
        "No interview ID found. Cannot start audio streaming and transcription."
      );
      return;
    }
    console.log(
      "Starting audio streaming and transcription for interviewId:",
      interviewId
    );

    //  Logic for audio streaming and transcription
    if (audioCtx.current.state === "suspended") {
      await audioCtx.current.resume();
    }

    let mediaRecorder;
    const dest = audioCtx.current.createMediaStreamDestination();

    try {
      // Check if navigator.mediaDevices and getUserMedia are available
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.error("Media Devices are not supported in this browser.");
        return;
      }

      const [micStream, displayStream] = await Promise.all([
        navigator.mediaDevices.getUserMedia({ audio: true }),
        navigator.mediaDevices
          .getDisplayMedia({
            video: { cursor: "always" },
            audio: { echoCancellation: true, noiseSuppression: true }, // Request audio with specific constraints
          })
          .catch((error) => {
            console.error("Error capturing screen with audio:", error);
            alert(
              "Failed to capture screen audio. Please ensure you've selected 'Share audio.'"
            );
            // Optionally, navigate away or handle error state
          }),
      ]);

      if (!MediaRecorder.isTypeSupported("audio/webm")) {
        alert("Browser not supported");
        return;
      }

      // Display the video stream
      if (displayStream.getVideoTracks().length > 0) {
        const videoElement = document.getElementById("sharedVideo");
        videoElement.srcObject = displayStream;
        videoElement.onloadedmetadata = () => {
          videoElement.play();
        };
      } else {
        console.error("No video tracks found in the display stream.");
        // Handle the case where no video is captured
      }

      [micStream, displayStream].forEach((stream) => {
        if (stream.getAudioTracks().length > 0) {
          const src = audioCtx.current.createMediaStreamSource(stream);
          src.connect(dest);
        } else {
          window.alert(
            "Warning: The selected stream contains no audio tracks. You will be redirected to the main board."
          );
          navigate("/Board"); // Navigate to the board page
        }
      });

      mediaRecorder = new MediaRecorder(dest.stream, {
        mimeType: "audio/webm",
      });
      mediaRecorderRef.current = mediaRecorder;

      if (!socketRef.current) {
        socketRef.current = new WebSocket(`${tranURL}`);
      }

      socketRef.current.onopen = () => {
        if (statusRef.current) statusRef.current.textContent = "Connected";
        mediaRecorder.addEventListener("dataavailable", (event) => {
          if (event.data.size > 0 && socketRef.current.readyState === 1) {
            socketRef.current.send(event.data);
          }
        });
        mediaRecorder.start(250); //sending blobs of data every 250ms
      };

      socketRef.current.onmessage = async (message) => {
        try {
          const receivedData = JSON.parse(message.data);
          // console.log(receivedData);

          if (receivedData && transcriptRef.current) {
            const {
              start,
              duration,
              transcript,
              confidence,
              speaker,
              channel,
            } = receivedData;

            const speakerText =
              speaker !== undefined ? `Speaker ${speaker}` : "Unknown Speaker";
            const formattedTranscript = `[${speakerText}] : ${transcript}`;

            const newLine = document.createElement("br");
            const newText = document.createTextNode(formattedTranscript);
            transcriptRef.current.appendChild(newLine);
            transcriptRef.current.appendChild(newText);
            // Set the state to trigger useEffect
            setTranscriptUpdated(true);

            console.log(
              "Updating InterviewData:",
              start,
              duration,
              transcript,
              confidence,
              speaker,
              channel
            );
            // Call the update function with all necessary data
            await updateInterviewData({
              start,
              duration,
              transcript,
              confidence,
              speaker,
              channel,
            });
          }
        } catch (error) {
          console.error("Error parsing received data:", error);
        }
      };
      // Start the interval for generateKeyNotes
      generateKeyNotesIntervalRef.current = setInterval(() => {
        generateKeyNotes();
      }, 120000); // 2 minutes in milliseconds

      // Start the interval for generateQuestions
      generateQuestionsIntervalRef.current = setInterval(() => {
        generateQuestions();
      }, 180000); // 3 minutes in milliseconds
    } catch (error) {
      console.error("Error:", error);
    }
    // Cleanup function
    return () => {
      if (
        mediaRecorderRef.current &&
        mediaRecorderRef.current.state !== "inactive"
      ) {
        mediaRecorderRef.current.stop();
      }
      if (socketRef.current) {
        socketRef.current.close();
      }
      clearInterval(generateKeyNotesIntervalRef.current);
      clearInterval(generateQuestionsIntervalRef.current);
    };
  };

  // Function to update interview data
  const updateInterviewData = async ({
    start,
    duration,
    transcript,
    confidence,
    speaker,
    channel,
  }) => {
    const interviewId = sessionStorage.getItem("interviewId");
    if (!interviewId) {
      console.error("No interview ID found. Cannot update interview data.");
      return;
    }

    const updateData = {
      _id: interviewId,
      transcription: {
        start, // Use the start time from the argument
        duration, // Use the duration from the argument
        transcript, // Use the transcript from the argument
        confidence, // Use the confidence value from the argument
        speaker, // Use the speaker value from the argument
        channel, // Use the channel value from the argument
      },
    };

    try {
      const response = await fetch(`${apiUrl}/interview/update`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        if (response.status === 422) {
          // Navigate to login page only if response status is 422
          navigate("/login");
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const responseJson = await response.json();
      // console.log("Update request response:", responseJson);
    } catch (error) {
      console.error("Error during update request:", error);
    }
  };

  // Function to stop audio streaming and transcription
  const stopAudioStreamingAndTranscription = async () => {
    // Stop MediaRecorder if it's recording
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state === "recording"
    ) {
      mediaRecorderRef.current.stop();
    }

    // Close WebSocket connection if it's open
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.close();
    }

    // Clear the interval for generating keynotes
    if (generateKeyNotesIntervalRef.current) {
      clearInterval(generateKeyNotesIntervalRef.current);
      generateKeyNotesIntervalRef.current = null;
    }

    // Clear the interval for generating questions
    if (generateQuestionsIntervalRef.current) {
      clearInterval(generateQuestionsIntervalRef.current);
      generateQuestionsIntervalRef.current = null;
    }

    // Additional cleanup (if needed)
    // ...

    // Call the API to mark the interview as finished
    const interviewId = sessionStorage.getItem("interviewId");
    if (interviewId) {
      try {
        // Existing logic to call the API and mark the interview as finished

        const response = await fetch(`${apiUrl}/interview/finish`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ _id: interviewId }),
        });

        setIsLoading(false); // Stop loading right before navigating
        // Check if the response is ok and navigate to archived meeting
        if (response.ok) {
          navigate(`/archived-meeting/${interviewId}`);
        } else {
          if (response.status === 422) {
            // Navigate to login page only if response status is 422
            navigate("/login");
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }
      } catch (error) {
        console.error("Error during finish interview request:", error);
        setIsLoading(false);
      }
    } else {
      // Ensure loading is stopped if interviewId is not found
      setIsLoading(false);
    }
  };

  // Function to call /get_notes API
  const generateKeyNotes = async () => {
    const interviewId = sessionStorage.getItem("interviewId");
    console.log("Attemtping to get interview key notes");
    if (!interviewId) {
      console.error("No interview ID found. Cannot generate keynotes.");
      return;
    }

    const requestData = {
      _id: interviewId,
    };

    try {
      const response = await fetch(`${apiUrl}/interview/get_notes`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      });

      console.log("request data:", JSON.stringify(requestData));

      if (!response.ok) {
        if (response.status === 422) {
          // Navigate to login page only if response status is 422
          navigate("/login");
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const keyNotesResponseJson = await response.json();

      // Check if keyNotesResponseJson contains a 'keynotes' string
      if (
        typeof keyNotesResponseJson.keynotes === "string" &&
        keyNotesResponseJson.keynotes.trim() !== ""
      ) {
        setKeyNotes((prevKeyNotes) => [
          keyNotesResponseJson.keynotes, // Add new keynote at the beginning
          ...prevKeyNotes, // Existing keynotes pushed down
        ]);
      } else {
        console.error("Error: 'keynotes' is not a string in the response");
      }
    } catch (error) {
      console.error("Error during keynotes request:", error);
    }
  };

  const generateQuestions = async () => {
    const interviewId = sessionStorage.getItem("interviewId");
    if (!interviewId) {
      console.error("No interview ID found. Cannot generate questions.");
      return;
    }

    const requestData = { _id: interviewId };

    try {
      const response = await fetch(`${apiUrl}/interview/get_questions`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        if (response.status === 422) {
          // Navigate to login page only if response status is 422
          navigate("/login");
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const questionsResponseJson = await response.json();
      if (
        questionsResponseJson.questions &&
        Array.isArray(questionsResponseJson.questions)
      ) {
        setQuestions(questionsResponseJson.questions);
      } else {
        console.error("Error: 'questions' key not found in the response");
      }
    } catch (error) {
      console.error("Error during questions request:", error);
    }
  };

  // Function to start recording
  const startRecording = async () => {
    const getCurrentDateTime = () => {
      const now = new Date();
      const date = now.toISOString().split("T")[0]; // Format: YYYY-MM-DD
      const time = now.toTimeString().split(" ")[0]; // Format: HH:MM:SS
      return { date, time };
    };

    // Get current date and time
    const startTime = getCurrentDateTime();
    // Send POST request with the current date and time
    // await AddInterviewPostRequest(startTime);
    await startAudioStreamingAndTranscription();
  };

  const stopRecording = async () => {
    setIsRecording(false); // Set recording state to false
    await stopAudioStreamingAndTranscription(); // Await completion
  };

  const handleButtonClick = async () => {
    if (isRecording) {
      const isConfirmed = window.confirm(
        "Are you sure you want to stop the interview?"
      );
      if (isConfirmed) {
        setIsLoading(true); // Start loading
        await stopRecording(); // Wait for the stopping process to complete
      }
    } else {
      startRecording();
    }
  };

  const onDetailsSubmit = (data) => {
    console.log("Details submitted:", data);
    setInterviewName(data.name);
    setInterviewTitle(data.title);
    setInterviewCompanyName(data.company_name);
    setInterviewDate(data.date);
    // Update other states as needed
  };

  useEffect(() => {
    audioCtx.current = new AudioContext();
  }, []);

  useEffect(() => {
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    // Retrieve the stored data from sessionStorage
    const storedData = sessionStorage.getItem("interviewDetails");

    // Parse the data back into an object
    const interviewDetails = storedData ? JSON.parse(storedData) : null;

    if (interviewDetails) {
      // Use interviewDetails to set the initial form values or state
      // Example: setName(interviewDetails.name);
    }
  }, []);

  const toggleAnswerVisibility = (questionId) => {
    if (expandedQuestionId === questionId) {
      // If the current question is already expanded, hide it
      setExpandedQuestionId(null);
    } else {
      // Otherwise, expand the new question
      setExpandedQuestionId(questionId);
    }
  };

  const isAnswerVisible = (questionId) => {
    return expandedQuestionId === questionId;
  };

  useEffect(() => {
    const handleBeforeUnload = (event) => {
      // Call your function to stop audio streaming here
      stopAudioStreamingAndTranscription();
      // For beforeunload to work
      event.preventDefault();
      event.returnValue = "";
    };

    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, []);

  // Effect hook to automatically scroll to the bottom of transcript section
  useEffect(() => {
    if (transcriptUpdated && transcriptRef.current) {
      setTimeout(() => {
        transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
      }, 100); // Delay of 100ms

      // Reset the state
      setTranscriptUpdated(false);
    }
  }, [transcriptUpdated]);
  return (
    <>
      {isLoading && (
        <div className="loading-overlay">
          <div className="spinner"></div>
        </div>
      )}

      <>
        <div className="main">
          <FarpointSidebar />
          {
            <div className="main-content">
              <div className="info">
                <div className="headings">
                  <h1>Meeting Dashboard</h1>
                  <h4>Information about meeting is here</h4>
                </div>
              </div>
              <div className="dashboard">
                <div className="dashboard-board">
                  <div className="details">
                    <div className="card">
                      <div className="card-details">
                        <h2 className="card-title">Attendees</h2>
                        <p className="card-count">{interviewName}</p>
                      </div>
                    </div>
                    <div className="card">
                      <div className="card-details">
                        <h2 className="card-title">Titles</h2>
                        <p className="card-count">{interviewTitle}</p>
                      </div>
                    </div>
                    <div className="card">
                      <div className="card-details">
                        <h2 className="card-title">Company Name</h2>
                        <p className="card-count">{interviewCompanyName}</p>
                      </div>
                    </div>
                    <div className="card">
                      <div className="card-details">
                        <h2 className="card-title">Date</h2>
                        <p className="card-count">{interviewDate}</p>
                      </div>
                    </div>
                  </div>
                  <div className="interview-transcripts-notes">
                    <div className="transcripts-notes">
                      <div className="transcript-meeting-section">
                        <div className="video-placeholder">
                          <video
                            id="sharedVideo"
                            playsInline
                            autoPlay
                            muted
                          ></video>
                        </div>
                        <h4 className="transcript-heading">Transcript Notes</h4>
                        <section
                          ref={transcriptRef}
                          className="transcript-section"
                        ></section>
                      </div>

                      <section className="keynotes-section">
                        <h2>Key Notes</h2>
                        <div className="keypoints">
                          {keyNotes.map((note, index) => (
                            <div key={index} className="keynote-card">
                              <p className="note-text">{note}</p>
                            </div>
                          ))}
                        </div>
                      </section>
                    </div>
                    <button
                      type="button"
                      className={`start-interview-btn ${
                        isRecording ? "stop-interview-btn" : ""
                      }`}
                      onClick={handleButtonClick}
                    >
                      {isRecording ? "Stop Meeting" : "Start Meeting"}
                    </button>
                  </div>
                </div>

                <div className="questions-and-completed">
                  <div className="questions">
                    <h2 className="questions-activity-title">
                      Recommended Questions
                    </h2>
                    <div className="questions-activities">
                      {questions.length > 0 ? (
                        questions.map((question, index) => (
                          <div key={index} className="questions-activity-item">
                            <div className="questions-content">
                              <span
                                className={`status-indicator ${
                                  question.answered ? "answered" : "pending"
                                }`}
                              />
                              <div className="question-and-action">
                                <p className="questions-comment">
                                  {question.question}
                                </p>
                                {question.answered && (
                                  <button
                                    className="expand-answer-button"
                                    onClick={() =>
                                      toggleAnswerVisibility(question.id)
                                    }
                                  >
                                    {isAnswerVisible(question.id)
                                      ? "Hide Answer"
                                      : "Show Answer"}
                                  </button>
                                )}
                              </div>
                            </div>
                            {isAnswerVisible(question.id) && (
                              <div className="answer-card">
                                <div className="answer-content">
                                  {question.answer}
                                </div>
                              </div>
                            )}
                          </div>
                        ))
                      ) : (
                        <p>No questions available yet.</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          }
        </div>
        <Modal
          isOpen={isModalOpen}
          setIsModalOpen={setIsModalOpen}
          onDetailsSubmit={onDetailsSubmit}
        />
      </>
    </>
  );
};

export default InterviewBoard;
