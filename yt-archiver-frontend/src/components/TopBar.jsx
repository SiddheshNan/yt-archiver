import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import IconButton from "@mui/material/IconButton";
import InputBase from "@mui/material/InputBase";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { Icon } from "@iconify/react";

export default function TopBar() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    const q = query.trim();
    if (q) {
      navigate(`/search?q=${encodeURIComponent(q)}`);
    }
  };

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        bgcolor: "#0f0f0f",
        borderBottom: "1px solid rgba(255,255,255,0.1)",
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar sx={{ gap: 2, px: { xs: 1, sm: 2 } }}>
        {/* Logo */}
        <Box
          sx={{ display: "flex", alignItems: "center", gap: 1, cursor: "pointer", flexShrink: 0 }}
          onClick={() => navigate("/")}
        >
          <Icon icon="mdi:youtube" width={32} color="#FF0000" />
          <Typography
            variant="h6"
            sx={{
              fontWeight: 700,
              letterSpacing: -0.5,
              display: { xs: "none", sm: "block" },
              color: "#fff",
            }}
          >
            Archiver
          </Typography>
        </Box>

        {/* Search Bar — centered */}
        <Box
          component="form"
          onSubmit={handleSearch}
          sx={{
            display: "flex",
            flex: 1,
            maxWidth: 640,
            mx: "auto",
          }}
        >
          <InputBase
            placeholder="Search videos..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            sx={{
              flex: 1,
              bgcolor: "#121212",
              border: "1px solid rgba(255,255,255,0.2)",
              borderRight: "none",
              borderRadius: "20px 0 0 20px",
              px: 2,
              py: 0.5,
              color: "#fff",
              fontSize: 14,
              "&:focus-within": {
                borderColor: "#3EA6FF",
              },
            }}
          />
          <IconButton
            type="submit"
            sx={{
              bgcolor: "rgba(255,255,255,0.08)",
              border: "1px solid rgba(255,255,255,0.2)",
              borderRadius: "0 20px 20px 0",
              px: 2,
              "&:hover": { bgcolor: "rgba(255,255,255,0.15)" },
            }}
          >
            <Icon icon="mdi:magnify" width={22} color="#fff" />
          </IconButton>
        </Box>

        {/* Right actions */}
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, flexShrink: 0 }}>
          <IconButton onClick={() => navigate("/add")} sx={{ color: "#fff" }}>
            <Icon icon="mdi:plus-circle-outline" width={26} />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
