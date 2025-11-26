# Frontend Specification

## 1. State Management Strategy
* **Global Server State:** React Query (TanStack Query) for fetching/caching API data (Products, User Profile).
* **Global UI State:** Zustand or Redux Toolkit for shopping cart management and theme toggling.
* **Local State:** `useState` for form inputs.

## 2. Component Architecture (Atomic Design)
* **Atoms:** Buttons, Inputs, Labels.
* **Molecules:** SearchBar (Input + Button), ProductCard (Image + Title + Price).
* **Organisms:** Navbar, Footer, ProductGrid.
* **Pages:** LoginPage, Dashboard, ProductDetails.

## 3. Routing (React Router v6)
* `/login` - Public Route
* `/signup` - Public Route
* `/` - Protected Route (Requires Auth Token)
* `/products/:id` - Protected Route

## 4. API Integration Client
Use `axios` with an interceptor:
* **Request Interceptor:** Automatically attaches the JWT token from localStorage to every request header.
* **Response Interceptor:** Automatically handles `401` errors by redirecting the user to `/login`.