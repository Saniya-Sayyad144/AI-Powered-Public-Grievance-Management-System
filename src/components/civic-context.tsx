import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import {
  ApiError,
  civicApi,
  saveToken,
  type Category,
  type CivicRole,
  type CivicUser,
  type Complaint,
  type ComplaintStatus,
  type DashboardStats,
  type NotificationItem,
} from "@/lib/civic-api";

type CivicContextValue = {
  role: CivicRole;
  user: CivicUser | null;
  items: Complaint[];
  categories: Category[];
  dashboard: DashboardStats | null;
  notificationItems: NotificationItem[];
  notifications: number;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  setUser: (user: CivicUser | null) => void;
  updateStatus: (id: string, status: ComplaintStatus) => Promise<void>;
  markNotificationRead: (id: number) => Promise<void>;
  markRead: () => Promise<void>;
};

const CivicContext = createContext<CivicContextValue | null>(null);

export function CivicProvider({ children }: { children: ReactNode }) {
  const [user, setCurrentUser] = useState<CivicUser | null>(null);
  const [items, setItems] = useState<Complaint[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [dashboard, setDashboard] = useState<DashboardStats | null>(null);
  const [notificationItems, setNotificationItems] = useState<NotificationItem[]>([]);
  const [notifications, setNotifications] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    const [complaints, categoryData, dashboardData, notificationData] = await Promise.all([
      civicApi.complaints({ page_size: 100 }),
      civicApi.categories(),
      civicApi.dashboard(),
      civicApi.notifications(),
    ]);
    setItems(complaints.data);
    setCategories(categoryData);
    setDashboard(dashboardData);
    setNotificationItems(notificationData.data);
    setNotifications(notificationData.meta.unread);
  }

  async function refresh() {
    if (!user) return;
    setError(null);
    try {
      await loadData();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not load CivicPulse data");
    }
  }

  useEffect(() => {
    let active = true;
    const bootstrap = async () => {
      if (!localStorage.getItem("civicpulse.access-token")) {
        if (active) setLoading(false);
        return;
      }
      try {
        const currentUser = await civicApi.me();
        if (!active) return;
        setCurrentUser(currentUser);
        try {
          await loadData();
        } catch (cause) {
          if (active)
            setError(cause instanceof Error ? cause.message : "Could not load CivicPulse data");
        }
      } catch (cause) {
        saveToken(null);
        if (active)
          setError(
            cause instanceof ApiError ? cause.message : "Unable to connect to CivicPulse API",
          );
      } finally {
        if (active) setLoading(false);
      }
    };
    void bootstrap();
    return () => {
      active = false;
    };
  }, []);

  async function updateStatus(id: string, status: ComplaintStatus) {
    await civicApi.updateStatus(id, status);
    await refresh();
  }

  async function markRead() {
    try {
      await civicApi.markAllRead();
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not update notifications");
    }
  }

  async function markNotificationRead(id: number) {
    try {
      await civicApi.markNotificationRead(id);
      setNotificationItems((current) =>
        current.map((item) => (item.id === id ? { ...item, is_read: true } : item)),
      );
      setNotifications((current) => Math.max(0, current - 1));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not update notification");
    }
  }

  function updateUser(nextUser: CivicUser | null) {
    setCurrentUser(nextUser);
    setError(null);
    if (!nextUser) {
      setItems([]);
      setCategories([]);
      setDashboard(null);
      setNotificationItems([]);
      setNotifications(0);
      return;
    }
    void loadData().catch((cause: unknown) =>
      setError(cause instanceof Error ? cause.message : "Could not load CivicPulse data"),
    );
  }

  return (
    <CivicContext.Provider
      value={{
        role: user?.role ?? "citizen",
        user,
        items,
        categories,
        dashboard,
        notificationItems,
        notifications,
        loading,
        error,
        refresh,
        setUser: updateUser,
        updateStatus,
        markNotificationRead,
        markRead,
      }}
    >
      {children}
    </CivicContext.Provider>
  );
}

export function useCivic() {
  const value = useContext(CivicContext);
  if (!value) throw new Error("CivicProvider missing");
  return value;
}
