BEGIN;
CREATE TABLE "Wydzial" (
    "id" serial NOT NULL PRIMARY KEY,
    "nazwa" varchar(240) NOT NULL
)
;
CREATE TABLE "Kierunek" (
    "id" serial NOT NULL PRIMARY KEY,
    "nazwa" varchar(240) NOT NULL,
    "wydzial_id" integer NOT NULL REFERENCES "Wydzial" ("id") DEFERRABLE INITIALLY DEFERRED,
    "liczbaSemestrowInz" integer NOT NULL,
    "liczbaSemestrowMgr" integer NOT NULL
)
;
CREATE TABLE "Uzytkownik" (
    "id" serial NOT NULL PRIMARY KEY,
    "nick" varchar(60) NOT NULL,
    "imie" varchar(60) NOT NULL,
    "nazwisko" varchar(80) NOT NULL,
    "haslo" varchar(128) NOT NULL,
    "mail" varchar(200) NOT NULL,
    "ktoWprowadzil_id" integer NOT NULL,
    "dataUtworzenia" timestamp with time zone NOT NULL,
    "dataOstLogowania" timestamp with time zone NOT NULL,
    "dataOstZmianyHasla" timestamp with time zone NOT NULL,
    "dataOstZmianyDanych" timestamp with time zone NOT NULL,
    "ktoZmienilDane_id" integer NOT NULL,
    "ileMoichWydarzen" integer NOT NULL,
    "poziomDostepu" integer NOT NULL
)
;
ALTER TABLE "Uzytkownik" ADD CONSTRAINT "ktoWprowadzil_id_refs_id_65dcba05" FOREIGN KEY ("ktoWprowadzil_id") REFERENCES "Uzytkownik" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "Uzytkownik" ADD CONSTRAINT "ktoZmienilDane_id_refs_id_65dcba05" FOREIGN KEY ("ktoZmienilDane_id") REFERENCES "Uzytkownik" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "Prowadzacy" (
    "id" serial NOT NULL PRIMARY KEY,
    "imie" varchar(50) NOT NULL,
    "nazwisko" varchar(80) NOT NULL,
    "tytul" varchar(50) NOT NULL,
    "ktoWprowadzil_id" integer NOT NULL REFERENCES "Uzytkownik" ("id") DEFERRABLE INITIALLY DEFERRED,
    "dataUtworzenia" timestamp with time zone NOT NULL,
    "dataOstZmianyDanych" timestamp with time zone NOT NULL,
    "ktoZmienilDane_id" integer NOT NULL REFERENCES "Uzytkownik" ("id") DEFERRABLE INITIALLY DEFERRED,
    "konflikt" boolean NOT NULL
)
;
CREATE TABLE "Kurs" (
    "id" serial NOT NULL PRIMARY KEY,
    "nazwa" varchar(240) NOT NULL,
    "rodzaj" varchar(1) NOT NULL,
    "ects" integer NOT NULL
)
;
CREATE TABLE "Grupa" (
    "id" serial NOT NULL PRIMARY KEY,
    "kodGrupy" varchar(15) NOT NULL,
    "prowadzacy_id" integer NOT NULL REFERENCES "Prowadzacy" ("id") DEFERRABLE INITIALLY DEFERRED,
    "dzienTygodnia" varchar(15) NOT NULL,
    "parzystosc" varchar(2) NOT NULL,
    "godzinaOd" time,
    "godzinaDo" time,
    "miejsce" varchar(20) NOT NULL,
    "kurs_id" integer NOT NULL REFERENCES "Kurs" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE TABLE "Student" (
    "id" serial NOT NULL PRIMARY KEY,
    "uzytkownik_id" integer NOT NULL REFERENCES "Uzytkownik" ("id") DEFERRABLE INITIALLY DEFERRED,
    "indeks" varchar(10) NOT NULL,
    "czyAktywowano" boolean NOT NULL,
    "rodzajStudiow" integer NOT NULL
)
;
CREATE TABLE "Plan" (
    "id" serial NOT NULL PRIMARY KEY,
    "student_id" integer NOT NULL REFERENCES "Student" ("id") DEFERRABLE INITIALLY DEFERRED,
    "grupa_id" integer NOT NULL REFERENCES "Grupa" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE TABLE "KierunkiStudenta" (
    "id" serial NOT NULL PRIMARY KEY,
    "student_id" integer NOT NULL REFERENCES "Student" ("id") DEFERRABLE INITIALLY DEFERRED,
    "kierunek_id" integer NOT NULL REFERENCES "Kierunek" ("id") DEFERRABLE INITIALLY DEFERRED,
    "semestr" integer NOT NULL,
    "uprawnienia" integer NOT NULL
)
;
CREATE TABLE "Shoutbox" (
    "id" serial NOT NULL PRIMARY KEY,
    "uzytkownik_id" integer NOT NULL REFERENCES "Uzytkownik" ("id") DEFERRABLE INITIALLY DEFERRED,
    "tresc" varchar(240) NOT NULL,
    "data" timestamp with time zone NOT NULL,
    "czyWazne" boolean NOT NULL
)
;
CREATE TABLE "Wydarzenie" (
    "id" serial NOT NULL PRIMARY KEY,
    "nazwa" varchar(240) NOT NULL,
    "opis" varchar(240) NOT NULL,
    "dataWydarzenia" date NOT NULL,
    "godzinaOd" time,
    "godzinaDo" time,
    "dataDodaniaWyd" timestamp with time zone NOT NULL,
    "rodzajWydarzenia" integer NOT NULL,
    "grupa_id" integer REFERENCES "Grupa" ("id") DEFERRABLE INITIALLY DEFERRED,
    "dodal_id" integer NOT NULL REFERENCES "Uzytkownik" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE TABLE "AktualneWydarzenie" (
    "id" serial NOT NULL PRIMARY KEY,
    "stare_id" integer NOT NULL REFERENCES "Wydarzenie" ("id") DEFERRABLE INITIALLY DEFERRED,
    "nowe_id" integer NOT NULL REFERENCES "Wydarzenie" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE TABLE "NotatkaDoWydarzenia" (
    "id" serial NOT NULL PRIMARY KEY,
    "wydarzenie_id" integer NOT NULL REFERENCES "Wydarzenie" ("id") DEFERRABLE INITIALLY DEFERRED,
    "notatka" varchar(240) NOT NULL
)
;
CREATE TABLE "Kalendarz" (
    "id" serial NOT NULL PRIMARY KEY,
    "uzytkownik_id" integer NOT NULL REFERENCES "Uzytkownik" ("id") DEFERRABLE INITIALLY DEFERRED,
    "wydarzenie_id" integer NOT NULL REFERENCES "Wydarzenie" ("id") DEFERRABLE INITIALLY DEFERRED,
    "opis" varchar(240) NOT NULL
)
;
CREATE TABLE "KategoriaMiejsca" (
    "id" serial NOT NULL PRIMARY KEY,
    "nazwa" varchar(20) NOT NULL
)
;
CREATE TABLE "Miejsce" (
    "id" serial NOT NULL PRIMARY KEY,
    "kategoria_id" integer NOT NULL REFERENCES "KategoriaMiejsca" ("id") DEFERRABLE INITIALLY DEFERRED,
    "nazwa" varchar(40) NOT NULL,
    "adres" varchar(80) NOT NULL,
    "godzinyOtwarcia" varchar(180) NOT NULL,
    "telefon" varchar(40) NOT NULL,
    "x" varchar(40) NOT NULL,
    "y" varchar(40) NOT NULL
)
;
CREATE TABLE "Konsultacje" (
    "id" serial NOT NULL PRIMARY KEY,
    "prowadzacy_id" integer NOT NULL REFERENCES "Prowadzacy" ("id") DEFERRABLE INITIALLY DEFERRED,
    "dzienTygodnia" varchar(15) NOT NULL,
    "parzystosc" varchar(2) NOT NULL,
    "godzinaOd" time NOT NULL,
    "godzinaDo" time NOT NULL,
    "budynek_id" integer NOT NULL REFERENCES "Miejsce" ("id") DEFERRABLE INITIALLY DEFERRED,
    "sala" varchar(10) NOT NULL,
    "inneInformacje" varchar(200) NOT NULL,
    "dataOstZmianyDanych" timestamp with time zone NOT NULL,
    "ktoZmienilDane_id" integer NOT NULL REFERENCES "Uzytkownik" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE TABLE "Tydzien" (
    "id" serial NOT NULL PRIMARY KEY,
    "nrTygodnia" integer NOT NULL,
    "dataOd" date NOT NULL,
    "dataDo" date NOT NULL,
    "rokAkademicki" varchar(9) NOT NULL,
    "semestr" integer NOT NULL
)
;
CREATE TABLE "ZmianaDat" (
    "id" serial NOT NULL PRIMARY KEY,
    "data" timestamp with time zone NOT NULL,
    "tydzien_id" integer NOT NULL REFERENCES "Tydzien" ("id") DEFERRABLE INITIALLY DEFERRED,
    "nowyDzien" integer NOT NULL,
    "parzystosc" varchar(2) NOT NULL
)
;
CREATE TABLE "NotatkaDoPlanu" (
    "id" serial NOT NULL PRIMARY KEY,
    "grupa_id" integer NOT NULL REFERENCES "Grupa" ("id") DEFERRABLE INITIALLY DEFERRED,
    "tydzien_id" integer NOT NULL REFERENCES "Tydzien" ("id") DEFERRABLE INITIALLY DEFERRED,
    "notatka" varchar(240) NOT NULL
)
;
CREATE INDEX "Kierunek_wydzial_id" ON "Kierunek" ("wydzial_id");
CREATE INDEX "Uzytkownik_ktoWprowadzil_id" ON "Uzytkownik" ("ktoWprowadzil_id");
CREATE INDEX "Uzytkownik_ktoZmienilDane_id" ON "Uzytkownik" ("ktoZmienilDane_id");
CREATE INDEX "Prowadzacy_ktoWprowadzil_id" ON "Prowadzacy" ("ktoWprowadzil_id");
CREATE INDEX "Prowadzacy_ktoZmienilDane_id" ON "Prowadzacy" ("ktoZmienilDane_id");
CREATE INDEX "Grupa_prowadzacy_id" ON "Grupa" ("prowadzacy_id");
CREATE INDEX "Grupa_kurs_id" ON "Grupa" ("kurs_id");
CREATE INDEX "Student_uzytkownik_id" ON "Student" ("uzytkownik_id");
CREATE INDEX "Plan_student_id" ON "Plan" ("student_id");
CREATE INDEX "Plan_grupa_id" ON "Plan" ("grupa_id");
CREATE INDEX "KierunkiStudenta_student_id" ON "KierunkiStudenta" ("student_id");
CREATE INDEX "KierunkiStudenta_kierunek_id" ON "KierunkiStudenta" ("kierunek_id");
CREATE INDEX "Shoutbox_uzytkownik_id" ON "Shoutbox" ("uzytkownik_id");
CREATE INDEX "Wydarzenie_grupa_id" ON "Wydarzenie" ("grupa_id");
CREATE INDEX "Wydarzenie_dodal_id" ON "Wydarzenie" ("dodal_id");
CREATE INDEX "AktualneWydarzenie_stare_id" ON "AktualneWydarzenie" ("stare_id");
CREATE INDEX "AktualneWydarzenie_nowe_id" ON "AktualneWydarzenie" ("nowe_id");
CREATE INDEX "NotatkaDoWydarzenia_wydarzenie_id" ON "NotatkaDoWydarzenia" ("wydarzenie_id");
CREATE INDEX "Kalendarz_uzytkownik_id" ON "Kalendarz" ("uzytkownik_id");
CREATE INDEX "Kalendarz_wydarzenie_id" ON "Kalendarz" ("wydarzenie_id");
CREATE INDEX "Miejsce_kategoria_id" ON "Miejsce" ("kategoria_id");
CREATE INDEX "Konsultacje_prowadzacy_id" ON "Konsultacje" ("prowadzacy_id");
CREATE INDEX "Konsultacje_budynek_id" ON "Konsultacje" ("budynek_id");
CREATE INDEX "Konsultacje_ktoZmienilDane_id" ON "Konsultacje" ("ktoZmienilDane_id");
CREATE INDEX "ZmianaDat_tydzien_id" ON "ZmianaDat" ("tydzien_id");
CREATE INDEX "NotatkaDoPlanu_grupa_id" ON "NotatkaDoPlanu" ("grupa_id");
CREATE INDEX "NotatkaDoPlanu_tydzien_id" ON "NotatkaDoPlanu" ("tydzien_id");
COMMIT;
