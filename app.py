# ==============================
# RESULTS
# ==============================
st.markdown("## 🎯 Results")

if not results:
    st.warning("⚠️ No relevant results found")
else:
    for r in results:
        st.markdown("---")

        st.caption(
            f"⭐ Score: {r.get('score',0)} | "
            f"🎯 Role Match: {r.get('role_score',0)} | "
            f"⚡ Intent: {r.get('intent_score',0)}"
        )

        # Email highlight
        if r["email"] != "Not found":
            st.success(f"📧 {r['email']}")
        else:
            st.caption("No Email Found")

        # Content preview
        st.write(r["content"][:400])

        # Link
        st.markdown(f"[🔗 Open Post]({r['link']})")
