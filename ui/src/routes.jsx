import { Suspense } from "react";
import { Outlet, Navigate, useRoutes } from "react-router-dom";
import MainLayout from "@/layouts/MainLayout";

import HomePage from "@/pages/HomePage";
import WatchPage from "@/pages/WatchPage";
import ChannelPage from "@/pages/ChannelPage";
import SearchPage from "@/pages/SearchPage";
import AddVideoPage from "@/pages/AddVideoPage";

export function Router() {
  return useRoutes([
    {
      path: "/",
      element: (
        <MainLayout>
          <Suspense fallback={null}>
            <Outlet />
          </Suspense>
        </MainLayout>
      ),
      children: [
        { element: <HomePage />, index: true },
        { element: <WatchPage />, path: "watch/:id" },
        { element: <ChannelPage />, path: "channel/:id" },
        { element: <SearchPage />, path: "search" },
        { element: <AddVideoPage />, path: "add" },
      ],
    },
    {
      path: "*",
      element: <Navigate to="/" replace />,
    },
  ]);
}
