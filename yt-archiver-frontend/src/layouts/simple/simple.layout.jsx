import Link from "@mui/material/Link";
import Alert from "@mui/material/Alert";
import { RouterLink } from "@/components/RouterLink";
import { Logo } from "@/components/logo";
import { LayoutSection } from "@/components/layout-section";
import { HeaderSection } from "@/components/header-section";
import Box from "@mui/material/Box";
import { useTheme } from "@mui/material/styles";
import { layoutClasses } from "@/utils/classes";

// ----------------------------------------------------------------------

export function SimpleLayout({ sx, children, header, content }) {
  const layoutQuery = "md";

  return (
    <LayoutSection
      /** **************************************
       * Header
       *************************************** */
      headerSection={
        <HeaderSection
          layoutQuery={layoutQuery}
          slotProps={{ container: { maxWidth: false } }}
          sx={header?.sx}
          slots={{
            topArea: (
              <Alert severity="info" sx={{ display: "none", borderRadius: 0 }}>
                This is an info Alert.
              </Alert>
            ),
            leftArea: <Logo />,
            rightArea: (
              <Link href="#" component={RouterLink} color="inherit" sx={{ typography: "subtitle2" }}>
                Need help?
              </Link>
            ),
          }}
        />
      }
      /** **************************************
       * Footer
       *************************************** */
      footerSection={null}
      /** **************************************
       * Style
       *************************************** */
      cssVars={{
        "--layout-simple-content-compact-width": "448px",
      }}
      sx={sx}
    >
      <Main>{content?.compact ? <CompactContent layoutQuery={layoutQuery}>{children}</CompactContent> : children}</Main>
    </LayoutSection>
  );
}

// ----------------------------------------------------------------------

export function Main({ children, sx, ...other }) {
  return (
    <Box
      component="main"
      className={layoutClasses.main}
      sx={{
        display: "flex",
        flex: "1 1 auto",
        flexDirection: "column",
        ...sx,
      }}
      {...other}
    >
      {children}
    </Box>
  );
}

// ----------------------------------------------------------------------

export function CompactContent({ sx, layoutQuery, children, ...other }) {
  const theme = useTheme();

  return (
    <Box
      className={layoutClasses.content}
      sx={{
        width: 1,
        mx: "auto",
        display: "flex",
        flex: "1 1 auto",
        textAlign: "center",
        flexDirection: "column",
        p: theme.spacing(3, 2, 10, 2),
        maxWidth: "var(--layout-simple-content-compact-width)",
        [theme.breakpoints.up(layoutQuery)]: {
          justifyContent: "center",
          p: theme.spacing(10, 0, 10, 0),
        },
        ...sx,
      }}
      {...other}
    >
      {children}
    </Box>
  );
}
