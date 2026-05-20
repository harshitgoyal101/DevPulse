export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  date_joined: string;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}
