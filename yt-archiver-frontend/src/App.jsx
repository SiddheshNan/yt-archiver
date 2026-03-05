import "./global.css";
import { Router } from "@/routes";
import { useScrollToTop } from "@/hooks/scrollToTop";
import { ThemeProvider } from "@/theme/theme-provider";
import { ToastContainer } from "react-toastify";

export default function App() {
  useScrollToTop();

  return (
    <>
      <ToastContainer
        position="bottom-right"
        theme="dark"
        toastStyle={{ background: "#272727", color: "#fff" }}
      />
      <ThemeProvider>
        <Router />
      </ThemeProvider>
    </>
  );
}
