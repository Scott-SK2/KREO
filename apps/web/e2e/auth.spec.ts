import { expect, test } from "@playwright/test";

test.describe("Authentification", () => {
  test("la page d'inscription expose les champs obligatoires", async ({ page }) => {
    await page.goto("/inscription");
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Créer ton compte");
    await expect(page.getByLabel("Code d'invitation")).toBeVisible();
    await expect(page.getByLabel("Adresse e-mail")).toBeVisible();
    await expect(page.getByLabel("Mot de passe", { exact: true })).toBeVisible();
    await expect(page.getByLabel("Date de naissance")).toBeVisible();
    await page.getByRole("button", { name: "Afficher le mot de passe" }).click();
    await expect(page.getByLabel("Mot de passe", { exact: true })).toHaveAttribute("type", "text");
  });

  test("une page privée redirige vers la connexion avec le paramètre next", async ({ page }) => {
    await page.goto("/tableau-de-bord");
    await expect(page).toHaveURL(/\/connexion\?next=%2Ftableau-de-bord/);
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Content de te revoir");
  });
});
