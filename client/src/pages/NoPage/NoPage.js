import React from "react";

import logo from "../../assets/farpoint_logo.svg";

import Navbar from "../../components/Navbar/Navbar";
import Footer from "../../components/Footer/Footer";
import "./NoPage.css";

const NoPage = () => {
  return (
    <div className="home">
      <header>
        <div className="wrapper">
          <Navbar />
          <div className="cta">
            <h1 className="welcome">Error 404: Page doesn't exist</h1>
          </div>
        </div>
      </header>
      <Footer />
    </div>
  );
};

export default NoPage;
