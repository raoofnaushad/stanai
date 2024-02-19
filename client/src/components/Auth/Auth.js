import { useNavigate } from "react-router-dom";

export const useAuth = () => {
  const navigate = useNavigate();
  const apiUrl = process.env.REACT_APP_API_URL;

  const refreshToken = async () => {
    const refresh_token = localStorage.getItem("refresh_token");

    const response = await fetch(`${apiUrl}/token/refresh`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${refresh_token}`,
      },
    });

    if (response.ok) {
      const data = await response.json();
      localStorage.setItem("access_token", data.access_token);
      return data.access_token;
    } else {
      navigate("/login");
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  };

  // Add other auth-related functions here

  return {
    refreshToken,
    // other functions
  };
};
