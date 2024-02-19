import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./FarpointSidebar.css";
import { useAuth } from "../Auth/Auth";

const InterviewSidebar = () => {
  const [userName, setUserName] = useState("");
  const navigate = useNavigate();
  const { refreshToken } = useAuth();
  const apiUrl = process.env.REACT_APP_API_URL;

  const fetchUserInfo = async (retryCount = 0) => {
    const token = localStorage.getItem("access_token");

    try {
      const response = await fetch(`${apiUrl}/userinfo`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log(data);
        setUserName(data.user); // Assuming the response contains a 'user' field
      } else if (response.status === 401 && retryCount < 2) {
        // Attempt to refresh token and retry
        await refreshToken();
        fetchUserInfo(retryCount + 1);
      } else {
        // Redirect to login after 2 failed retries
        navigate("/login");
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      navigate("/login");
      console.error("Error fetching user info:", error);
    }
  };

  useEffect(() => {
    fetchUserInfo();
  }, []);

  const handleFarpointBOT = () => {
    navigate("/FarpointBOT");
  };

  const handleInterviewBoard = () => {
    navigate("/Board");
  };

  const handleLogout = () => {
    // Clear the token from local storage
    localStorage.removeItem("access_token");

    // Use navigate to redirect to the Login page
    navigate("/Login");
  };

  return (
    <div className="sidebar">
      <a href="PromptLibrary" className="sidebar-logo-link">
        <h1>FarpointOI</h1>
      </a>
      <div className="sidebar-top">
        <button type="button" onClick={handleFarpointBOT}>
          Farpoint BOT
        </button>
        <button type="button" onClick={handleInterviewBoard}>
          Meeting Board
        </button>
      </div>
      <div className="sidebar-bottom">
        <button type="button">Settings</button>
        <button type="button">Help</button>
        <button className="logout-btn" onClick={handleLogout}>
          Log out
        </button>
        {userName && <p className="user-name">{userName}</p>}{" "}
      </div>
    </div>
  );
};

export default InterviewSidebar;
