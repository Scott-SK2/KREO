import { expect, test } from "@playwright/test";

test.describe("Accueil", () => {
  test("affiche le slogan, les deux appels à l'action et le lien d'évitement", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1 })).toContainText(
      "Une idée, des talents, un projet.",
    );
    await expect(page.getByRole("link", { name: "Voir les annonces" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Rejoindre la bêta" })).toBeVisible();
    await page.keyboard.press("Tab");
    await expect(page.getByRole("link", { name: "Aller au contenu" })).toBeFocused();
  });

  test("mène à la découverte avec des filtres partageables", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Voir les annonces" }).first().click();
    await expect(page).toHaveURL(/\/decouvrir$/);
    await page.getByRole("tab", { name: "Projets" }).click();
    await expect(page).toHaveURL(/onglet=projets/);
  });
});
