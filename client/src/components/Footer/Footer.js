import React from "react";
import "./Footer.css";

const Footer = () => {
  return (
    <footer className="black">
      <div className="wrapper">
        <div className="content-container">
          <div className="company-rights">
            <a href="#" className="logo-white">
              Farpoint Technologies
            </a>
            <div className="copyright">
              © 2023 Farpoint Technologies Inc. All rights reserved.
            </div>
          </div>

          <div className="links">
            <h3>Navigation</h3>
            <ul>
              <li>
                <a href="#">Who We Are</a>
              </li>
              <li>
                <a href="#">What We Do</a>
              </li>
              <li>
                <a href="#">Our Impact</a>
              </li>
            </ul>
          </div>

          <div className="links">
            <h3>Quick Links</h3>
            <ul>
              <li>
                <a href="#">Terms & Conditions</a>
              </li>
              <li>
                <a href="#">Privacy Policies</a>
              </li>
              <li>
                <a href="#">Contact</a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
