import React, { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import { useGoogleLogin } from "@react-oauth/google";

import logo from "../../assets/farpoint_logo.svg";

import Navbar from "../../components/Navbar/Navbar";
import Footer from "../../components/Footer/Footer";
import "./Login.css";

async function getUserInfo(codeResponse) {
  const apiUrl = process.env.REACT_APP_API_URL;
  // console.log("APIURL is:", apiUrl);
  var response = await fetch(`${apiUrl}/google_login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ code: codeResponse.code }),
  });
  const data = await response.json();

  // Store JWT token in local storage
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);

  return data;
}

const Login = () => {
  const [loggedIn, setLoggedIn] = useState(false);
  const [user, setUser] = useState({});
  const navigate = useNavigate();
  // Define your scopes as a space-separated string
  const scopes = [
    "openid",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
  ].join(" ");
  const googleLogin = useGoogleLogin({
    flow: "auth-code",
    scope: scopes, // Include the scopes in your request
    onSuccess: async (codeResponse) => {
      var loginDetails = await getUserInfo(codeResponse);
      setLoggedIn(true);
      setUser(loginDetails.user);
      navigate("/");
    },
  });

  const apiUrl = process.env.REACT_APP_API_URL;

  useEffect(() => {
    const checkIfLoggedIn = async () => {
      const token = localStorage.getItem("access_token");
      if (!token) return;

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
          setLoggedIn(true);
          setUser(data.user);
          navigate("/");
        } else {
          // If not logged in, remove any potentially invalid tokens
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
        }
      } catch (error) {
        console.error("Error fetching user info:", error);
      }
    };

    checkIfLoggedIn();
  }, [navigate]);

  return (
    <div className="home">
      <header>
        <div className="wrapper">
          <Navbar />
          <div className="cta">
            <img className="logo" src={logo} alt="Logo"></img>
            <h1 className="welcome">Welcome back to FarpointOI</h1>
            <p className="message">Login into your google account</p>
            <div className="google-btn-container">
              <button className="google-btn" onClick={googleLogin}>
                Google
              </button>
            </div>
            <p>
              Don't have an account? <Link to="/Signup">Sign up!</Link>
            </p>
          </div>
        </div>
      </header>
      <Footer />
    </div>
  );
};

export default Login;
