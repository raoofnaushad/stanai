import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";

import {
  Home,
  Login,
  NoPage,
  Signup,
  FarpointBOT,
  Board,
  InterviewBoard,
  ArchivedMeeting,
} from "./pages";

const App = () => {
  return (
    <GoogleOAuthProvider clientId="463029741850-q0p6vmfdmhvk4os7ceglpgkkovkkcqau.apps.googleusercontent.com">
      <BrowserRouter>
        <Routes>
          <Route index element={<FarpointBOT />}></Route>
          {/* <Route path="/home" element={<Home />}></Route> */}
          <Route path="/login" element={<Login />}></Route>
          <Route path="/signup" element={<Signup />}></Route>
          <Route path="/FarpointBOT" element={<FarpointBOT />}></Route>
          <Route path="/Board" element={<Board />}></Route>
          <Route path="/InterviewBoard" element={<InterviewBoard />}></Route>
          <Route
            path="/archived-meeting/:meeting_id"
            element={<ArchivedMeeting />}
          />
          <Route path="*" element={<NoPage />}></Route>
        </Routes>
      </BrowserRouter>
    </GoogleOAuthProvider>
  );
};

export default App;
