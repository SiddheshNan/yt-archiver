import { Label } from "@/components/label";
import { SvgColor } from "@/components/svg-color";
import { Iconify } from "@/components/iconify";
import CameraAltIcon from "@mui/icons-material/CameraAlt";
import ArticleIcon from "@mui/icons-material/Article";
import LockIcon from "@mui/icons-material/Lock";
import GroupIcon from "@mui/icons-material/Group";
import SettingsIcon from "@mui/icons-material/Settings";
import BuildIcon from "@mui/icons-material/Build";
import SettingsBackupRestoreIcon from "@mui/icons-material/SettingsBackupRestore";
import BackupTableIcon from "@mui/icons-material/BackupTable";
import SdCardIcon from "@mui/icons-material/SdCard";
import CableIcon from "@mui/icons-material/Cable";

export const navData = [
  {
    title: "Perform Test",
    path: "/dashboard",
    icon: <CameraAltIcon icon="mdi:camera" width={25} height={25} />,
    permissions: ["RUN_TEST_CYCLE"],
  },

  {
    title: "Cycle Reports",
    path: "/dashboard/reports",
    icon: <ArticleIcon icon="mdi:file-chart" width={25} height={25} />,
    permissions: ["VIEW_CYCLE_REPORTS"],
  },

  {
    title: "Audit Trail",
    path: "/dashboard/audit-trail",
    icon: <LockIcon icon="mdi:lock-outline" width={25} height={25} />,
    permissions: ["VIEW_AUDIT_TRAIL"],
  },
  {
    title: "Users Management",
    path: "/dashboard/user-management",
    icon: <GroupIcon icon="mdi:account-cog-outline" width={25} height={25} />,
    permissions: ["USER_MANAGEMENT"],
  },

  {
    title: "App Settings",
    path: "/dashboard/app-settings",
    icon: <SettingsIcon icon="mdi:settings-outline" width={25} height={25} />,
    permissions: ["APP_SETTINGS_MANAGEMENT"],
  },

  {
    title: "Calibrate & Verify",
    path: "/dashboard/calibration",
    icon: <BuildIcon icon="mdi:wrench-outline" width={25} height={25} />,
    permissions: ["WEIGHT_CALIBRATION", "NEEDLE_DEPTH_VERIFICATION"],
  },

  {
    title: "Backup & Restore",
    path: "/dashboard/backup-restore",
    icon: <BackupTableIcon width={25} height={25} />,
    permissions: ["BACKUP_AND_RESTORE"],
  },

  {
    title: "Hardware Connectivity",
    path: "/dashboard/device-connection-status",
    icon: <CableIcon width={25} height={25} />,
    permissions: ["HARDWARE_CONNECTIVITY_STATUS"],
  },
];
