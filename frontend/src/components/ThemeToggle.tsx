"use client";

import { useTheme } from "@/context/ThemeContext";
import { FiMoon, FiSun } from "react-icons/fi";

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-md text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
      title={theme === "light" ? "Ativar modo escuro" : "Ativar modo claro"}
    >
      {theme === "light" ? <FiMoon size={20} /> : <FiSun size={20} />}
    </button>
  );
}
