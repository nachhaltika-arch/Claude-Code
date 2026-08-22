// Wird von react-scripts vor jedem Testlauf geladen.
//
// `jest-dom` bringt die Zusicherungen, die auf dem DOM arbeiten —
// `toBeInTheDocument`, `toHaveAttribute`, `toHaveTextContent`. Ohne sie
// liessen sich Komponenten nur ueber Umwege pruefen.
//
// Angelegt am 22.08.2026 mit L-83. Bis dahin hatte das Frontend nur Tests
// fuer reine Funktionen — und genau deshalb konnte L-79 passieren: Der Knopf
// „Freigabe anfordern" stand fertig da und hatte kein `onClick`. Ein
// Rendertest haette das in einer Zeile gemeldet.
import '@testing-library/jest-dom';
