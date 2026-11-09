"use client";

import type { components } from "@kreo/api-client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { SendHorizontal } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useId, useMemo, useRef, useState, type FormEvent } from "react";

import { SafetyTips } from "@/components/SafetyTips";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { useToast } from "@/components/ui/Toast";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { useMe } from "@/hooks/useMe";
import { api, unwrap } from "@/lib/api/client";
import { cn } from "@/lib/cn";
import { formatDateTime } from "@/lib/format";

import { CONVERSATIONS_KEY } from "./ConversationList";

type Message = components["schemas"]["Message"];
type Conversation = components["schemas"]["Conversation"];

const POLL_MS = 15_000;

/**
 * Fil de discussion : chargement initial, interrogation toutes les 15 s avec
 * `?after=` (dernier message connu), marquage lu à l'ouverture, composeur.
 * Les conseils de sécurité restent affichés tant qu'aucun message n'existe.
 */
export function ConversationThread({ conversation }: { conversation: Conversation }) {
  const t = useTranslations("messages");
  const describeError = useErrorMessage();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const me = useMe();
  const id = useId();
  const [messages, setMessages] = useState<Message[]>([]);
  const [body, setBody] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const lastAt = useMemo(() => messages.at(-1)?.created_at, [messages]);

  const initial = useQuery({
    queryKey: ["conversation", conversation.id, "messages"],
    queryFn: async () =>
      unwrap(
        await api.GET("/api/v1/conversations/{conversation_id}/messages", {
          params: { path: { conversation_id: conversation.id } },
        }),
      ),
    staleTime: Infinity,
  });

  useEffect(() => {
    if (initial.data) setMessages(initial.data);
  }, [initial.data]);

  // Marquer comme lu à l'ouverture, puis rafraîchir les compteurs de la liste.
  useEffect(() => {
    api
      .POST("/api/v1/conversations/{conversation_id}/read", {
        params: { path: { conversation_id: conversation.id } },
      })
      .then(() => queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY }))
      .catch(() => undefined);
  }, [conversation.id, queryClient]);

  // Interrogation légère : seuls les messages postérieurs au dernier connu sont demandés.
  useEffect(() => {
    if (!initial.isSuccess) return;
    const timer = window.setInterval(async () => {
      try {
        const fresh = unwrap(
          await api.GET("/api/v1/conversations/{conversation_id}/messages", {
            params: { path: { conversation_id: conversation.id }, query: { after: lastAt } },
          }),
        );
        if (fresh.length) {
          setMessages((list) => {
            const known = new Set(list.map((m) => m.id));
            return [...list, ...fresh.filter((m) => !known.has(m.id))];
          });
          void api.POST("/api/v1/conversations/{conversation_id}/read", {
            params: { path: { conversation_id: conversation.id } },
          });
        }
      } catch {
        // Silencieux : on réessaie au prochain tour.
      }
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [conversation.id, initial.isSuccess, lastAt]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [messages.length]);

  const send = useMutation({
    mutationFn: async () =>
      unwrap(
        await api.POST("/api/v1/conversations/{conversation_id}/messages", {
          params: { path: { conversation_id: conversation.id } },
          body: { body: body.trim() },
        }),
      ),
    onSuccess: (message) => {
      setMessages((list) => (list.some((m) => m.id === message.id) ? list : [...list, message]));
      setBody("");
      void queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY });
    },
    onError: (error) => toast(describeError(error), "error"),
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!body.trim()) return;
    send.mutate();
  };

  const myId = me.data?.id;

  return (
    <div className="flex min-h-[60vh] flex-col rounded-xl border border-taupe/15 bg-white">
      <div className="border-b border-taupe/10 px-5 py-4">
        <h2 className="text-base normal-case tracking-normal">{conversation.project_title}</h2>
        <p className="text-sm text-taupe-dark">
          {t("conversationWith", { role: conversation.role_title })}
        </p>
      </div>

      <div
        className="flex-1 overflow-y-auto px-5 py-4"
        aria-live="polite"
        aria-relevant="additions"
      >
        {initial.isPending ? (
          <div className="flex flex-col gap-3" aria-busy="true">
            <Skeleton className="h-12 w-2/3" />
            <Skeleton className="ml-auto h-12 w-1/2" />
            <Skeleton className="h-12 w-3/5" />
          </div>
        ) : messages.length ? (
          <ol className="flex flex-col gap-3">
            {messages.map((m) => {
              const mine = m.sender_id === myId;
              return (
                <li key={m.id} className={cn("flex", mine ? "justify-end" : "justify-start")}>
                  <div
                    className={cn(
                      "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm",
                      mine
                        ? "rounded-br-sm bg-brown text-paper"
                        : "rounded-bl-sm bg-ivory text-brown",
                    )}
                  >
                    {!mine ? (
                      <p className="mb-0.5 text-xs font-medium opacity-80">
                        {m.sender.display_name}
                      </p>
                    ) : null}
                    <p className="whitespace-pre-line">{m.body}</p>
                    <p
                      className={cn("mt-1 text-[11px]", mine ? "text-paper/70" : "text-taupe-dark")}
                    >
                      {formatDateTime(m.created_at)}
                    </p>
                  </div>
                </li>
              );
            })}
            <div ref={bottomRef} />
          </ol>
        ) : (
          <p className="text-sm text-taupe-dark">{t("noMessages")}</p>
        )}
      </div>

      <div className="border-t border-taupe/10 p-4">
        {initial.isSuccess && messages.length === 0 ? (
          <SafetyTips tips={conversation.safety_tips} className="mb-4" />
        ) : null}
        <form onSubmit={submit} className="flex items-end gap-2">
          <label htmlFor={`${id}-body`} className="sr-only">
            {t("placeholder")}
          </label>
          <textarea
            id={`${id}-body`}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit(e);
            }}
            placeholder={t("placeholder")}
            rows={2}
            maxLength={4000}
            className="min-h-touch flex-1 resize-none rounded-md border border-taupe/40 bg-white px-3 py-2 text-base text-ink placeholder:text-taupe/70 hover:border-taupe"
          />
          <Button
            type="submit"
            loading={send.isPending}
            disabled={!body.trim()}
            icon={<SendHorizontal aria-hidden="true" className="size-4" strokeWidth={1.5} />}
            aria-label={t("send")}
          >
            <span className="hidden sm:inline">{t("send")}</span>
          </Button>
        </form>
        <p className="mt-2 text-xs text-taupe-dark">{t("polling")}</p>
      </div>
    </div>
  );
}
