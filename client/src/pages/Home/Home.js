import React from "react";
import { Link } from "react-router-dom";

import logo from "../../assets/farpoint_logo.svg";

import Navbar from "../../components/Navbar/Navbar";
import Footer from "../../components/Footer/Footer";
import "./Home.css";

const Home = () => {
  return (
    <div className="home">
      <header>
        <div className="wrapper">
          <Navbar />
          <div className="cta">
            <img className="logo" src={logo} alt="Logo"></img>
            <h1 className="welcome">Welcome to FarpointOS</h1>
            <p className="message">
              Signup or Login with your farpoint google account
            </p>
            <Link to="/Login" className="cta-btn">
              Log In
            </Link>
            <Link to="/Signup" className="cta-btn">
              Sign Up
            </Link>
          </div>
        </div>
      </header>
      <Footer />
    </div>
  );
};

export default Home;
