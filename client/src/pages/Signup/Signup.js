import React from "react";
import { Link } from "react-router-dom";
import { useNavigate } from "react-router-dom";

import logo from "../../assets/farpoint_logo.svg";

import Navbar from "../../components/Navbar/Navbar";
import Footer from "../../components/Footer/Footer";
import "./Signup.css";

const Signup = () => {
  const navigate = useNavigate();
  const handleClick = () => navigate("/PromptLibrary");

  return (
    <div className="home">
      <header>
        <div className="wrapper">
          <Navbar />
          <div className="cta">
            <img className="logo" src={logo} alt="Logo"></img>
            <h1 className="welcome">Get Started With FarpointOS</h1>
            <p className="message">Getting Started is easy</p>
            <div class="google-btn-container">
              <button class="google-btn" onClick={handleClick}>
                Google
              </button>
            </div>
            <p>
              Already have an account? <Link to="/Login">Sign in!</Link>
            </p>
          </div>
        </div>
      </header>
      <Footer />
    </div>
  );
};

export default Signup;
