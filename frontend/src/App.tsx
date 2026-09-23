import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import ChatPage from "./pages/chatPage";
import LoginPage from "./pages/loginPage";
import RegisterPage from "./pages/registerPage";
import { AuthStore } from "./stroes/authStroes";

function RequireAuth({ children }: { children: React.ReactElement }) {
  const status = AuthStore((s) => s.status);

  if (status === "idle" || status === "loading") {
    return (
      <div className="flex h-full items-center justify-center text-gray-500">
        Loading…
      </div>
    );
  }
  if (status !== "authentecated") return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  const bootstrap = AuthStore((s) => s.bootstrap);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <ChatPage />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
