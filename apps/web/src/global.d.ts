import type { Messages } from "@kreo/i18n";

declare module "next-intl" {
  interface AppConfig {
    Messages: Messages;
  }
}
