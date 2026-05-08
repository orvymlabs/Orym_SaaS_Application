#!/bin/bash
routes=(
  "/"
  "/login"
  "/signup"
  "/test"
  "/subscriptions"
  "/dashboard"
  "/dashboard/admin"
  "/dashboard/admin/announcements"
  "/dashboard/admin/logs"
  "/dashboard/admin/revenue"
  "/dashboard/admin/settings"
  "/dashboard/admin/users"
  "/dashboard/admin/users/view"
  "/dashboard/chats"
  "/dashboard/docs"
  "/dashboard/integrations"
  "/dashboard/leads"
  "/dashboard/orders"
  "/dashboard/settings"
  "/dashboard/subscription"
  "/dashboard/Support"
  "/dashboard/test-chat"
)

echo "Testing all routes on port 3002..."
success=0
failed=0
for route in "${routes[@]}"; do
  status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3002$route")
  if [[ "$status" == "200" || "$status" == "307" || "$status" == "308" ]]; then
    echo "✓ $route - HTTP $status"
    ((success++))
  else
    echo "✗ $route - HTTP $status"
    ((failed++))
  fi
done
echo ""
echo "Summary: $success passed, $failed failed"
