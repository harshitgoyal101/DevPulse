import { useCallback, useEffect, useState } from "react";
import { listMemberships } from "../api/organizations";
import { authErrorMessage } from "../context/AuthContext";
import type { Role } from "../types/organizations";

interface UseOrgMembershipResult {
  role: Role | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useOrgMembership(
  accessToken: string | null,
  orgId: string | null,
  userEmail: string | undefined,
): UseOrgMembershipResult {
  const [role, setRole] = useState<Role | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    if (!accessToken || !orgId || !userEmail) {
      setRole(null);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const memberships = await listMemberships(accessToken, orgId);
      const mine = memberships.find(
        (membership) => membership.email.toLowerCase() === userEmail.toLowerCase(),
      );
      setRole(mine?.role ?? null);
    } catch (err) {
      setRole(null);
      setError(authErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [accessToken, orgId, userEmail]);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { role, loading, error, refetch };
}
