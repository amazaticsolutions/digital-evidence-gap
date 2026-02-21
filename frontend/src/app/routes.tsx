import { createBrowserRouter, Navigate } from 'react-router';
import { MainLayout } from './layouts/MainLayout';
import { NewCase } from './pages/NewCase';
import { PastCases } from './pages/PastCases';
import { ChatWorkspace } from './pages/ChatWorkspace';

export const router = createBrowserRouter([
  {
    path: '/',
    Component: MainLayout,
    children: [
      {
        index: true,
        element: <Navigate to="/new-case" replace />,
      },
      {
        path: 'new-case',
        Component: NewCase,
      },
      {
        path: 'past-cases',
        Component: PastCases,
      },
      {
        path: 'case/:id',
        Component: ChatWorkspace,
      },
      {
        path: '*',
        element: <Navigate to="/new-case" replace />,
      },
    ],
  },
]);