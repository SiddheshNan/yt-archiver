import Box from "@mui/material/Box";
import Toolbar from "@mui/material/Toolbar";
import TopBar from "@/components/TopBar";

export default function MainLayout({ children }) {
  return (
    <Box sx={{ display: "flex", minHeight: "100vh", bgcolor: "#0f0f0f" }}>
      <TopBar />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: "100%",
          pt: { xs: 7, sm: 8 },
        }}
      >
        {children}
      </Box>
    </Box>
  );
}
