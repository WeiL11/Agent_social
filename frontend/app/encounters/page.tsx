import { redirect } from "next/navigation";

// 邂逅已併入任務回報頁（閒逛發現）。
export default function EncountersRedirect() {
  redirect("/missions");
}
