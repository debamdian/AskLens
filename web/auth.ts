import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import Google from "next-auth/providers/google";
import { SignJWT } from "jose";

interface DemoUser {
  id: string;
  email: string;
  name: string;
  role: "admin" | "analyst" | "sales_manager";
  regionId?: number;
  password: string;
}

const DEMO_USERS: DemoUser[] = [
  {
    id: "1",
    email: "admin@asklens.ai",
    name: "AskLens Admin",
    role: "admin",
    password: process.env.DEMO_ADMIN_PASSWORD || "admin123",
  },
  {
    id: "2",
    email: "analyst@asklens.ai",
    name: "Senior Analyst",
    role: "analyst",
    password: process.env.DEMO_ANALYST_PASSWORD || "analyst123",
  },
  {
    id: "3",
    email: "sales@asklens.ai",
    name: "Gujarat Sales Manager",
    role: "sales_manager",
    regionId: 1,
    password: process.env.DEMO_SALES_PASSWORD || "sales123",
  },
];

async function signBackendJwt(payload: {
  email: string;
  role: string;
  name?: string;
  region_id?: number;
}): Promise<string> {
  const secret = new TextEncoder().encode(
    process.env.JWT_SECRET || "super_secret_jwt_key_change_me_in_production_min_32_chars"
  );
  return new SignJWT(payload)
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("24h")
    .sign(secret);
}

const providers = [
  Credentials({
    name: "Credentials",
    credentials: {
      email: { label: "Email", type: "email" },
      password: { label: "Password", type: "password" },
    },
    async authorize(credentials) {
      const email = String(credentials?.email || "").toLowerCase().trim();
      const password = String(credentials?.password || "");
      const found = DEMO_USERS.find(
        (u) => u.email.toLowerCase() === email && u.password === password
      );
      if (!found) return null;
      return {
        id: found.id,
        email: found.email,
        name: found.name,
        role: found.role,
        regionId: found.regionId,
      };
    },
  }),
  ...(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET
    ? [
        Google({
          clientId: process.env.GOOGLE_CLIENT_ID,
          clientSecret: process.env.GOOGLE_CLIENT_SECRET,
        }),
      ]
    : []),
];

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers,
  session: { strategy: "jwt" },
  secret: process.env.NEXTAUTH_SECRET || process.env.JWT_SECRET || "asklens_dev_nextauth_secret",
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        const u = user as unknown as { role?: string; regionId?: number };
        token.role = u.role || "analyst";
        token.regionId = u.regionId;
        token.backendToken = await signBackendJwt({
          email: String(user.email || "analyst@asklens.ai"),
          role: String(token.role),
          name: user.name || undefined,
          region_id: u.regionId,
        });
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        (session.user as unknown as Record<string, unknown>).role = token.role || "analyst";
        (session.user as unknown as Record<string, unknown>).regionId = token.regionId;
      }
      (session as unknown as Record<string, unknown>).backendToken = token.backendToken;
      return session;
    },
  },
});
