import React from "react";
import { Link } from "react-router-dom";

import "./Navbar.css";

const Navbar = () => {
  return (
    <nav>
      <Link to="/" className="logo">
        Farpoint<span className="red">OI</span>
      </Link>
      <ul>
        <li>
          <a href="#">About</a>
        </li>
        <li>
          <a href="#">Safety</a>
        </li>
        <li>
          <a href="https://www.farpointhq.com/" target="_blank">
            Company
          </a>
        </li>
      </ul>
    </nav>
  );
};

export default Navbar;
